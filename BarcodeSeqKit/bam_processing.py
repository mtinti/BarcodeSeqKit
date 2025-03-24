"""Processing BAM files for barcode extraction and classification"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_bam_processing.ipynb.

# %% auto 0
__all__ = ['BamUtils', 'extract_softclipped_region', 'process_bam_file', 'prepare_bam_categories', 'classify_read',
           'get_output_path', 'save_statistics']

# %% ../nbs/02_bam_processing.ipynb 4
import os
import re
import gzip
import logging
import shutil
from typing import List, Dict, Tuple, Set, Optional, Union, Iterator, Any, Counter
from pathlib import Path
import pysam
import tempfile
import numpy as np
from pysam import AlignmentFile, AlignedSegment
import subprocess
from tqdm.auto import tqdm

from BarcodeSeqKit.core import (
    BarcodeConfig, 
    BarcodeMatch, 
    OrientationType,
    ExtractionStatistics,
    BarcodeLocationType,
    BarcodeExtractorConfig
)
from .sequence_utils import classify_read_by_first_match

# %% ../nbs/02_bam_processing.ipynb 6
class BamUtils:
    """Utility functions for BAM file operations."""
    
    @staticmethod
    def sort_and_index(bam_file: str) -> None:
        """Sort and index a BAM file by reference.
        
        Args:
            bam_file: Path to the BAM file
        """
        # Create a temporary file for sorting
        temp_file = f"{bam_file}.temp.bam"
        
        # Sort the BAM file to a temporary file
        pysam.sort("-o", temp_file, bam_file)
        
        # Replace the original with the sorted file
        os.replace(temp_file, bam_file)
        
        # Index the BAM file
        pysam.index(bam_file)
    
    @staticmethod
    def get_read_count(bam_file: str) -> int:
        """Get the total number of reads in a BAM file.
        
        Args:
            bam_file: Path to the BAM file
            
        Returns:
            Total number of reads
        """
        # Run samtools idxstats to get read counts
        cmd = ["samtools", "idxstats", bam_file]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"Error running samtools idxstats: {result.stderr}")
            
            # Parse the output
            mapped = 0
            unmapped = 0
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 4:
                    mapped += int(parts[2])
                    unmapped += int(parts[3])
            
            return mapped + unmapped
        except Exception as e:
            # If samtools fails, use pysam as fallback
            with pysam.AlignmentFile(bam_file, "rb") as bam:
                try:
                    # Try to get count from header
                    return sum(bam.header.get("RG", {}).get("LB", 0) for rg in bam.header.get("RG", []))
                except:
                    # Just count the reads - slower but reliable
                    return sum(1 for _ in bam)
    
    @staticmethod
    def merge_bam_files(output_file: str, input_files: List[str]) -> None:
        """Merge multiple BAM files into one.
        
        Args:
            output_file: Path to the output BAM file
            input_files: List of input BAM file paths
        """
        if not input_files:
            return
        
        # Use pysam to merge the files
        pysam.merge("-f", output_file, *input_files)

# %% ../nbs/02_bam_processing.ipynb 8
def extract_softclipped_region(read):
    """
    Extracts softclipped regions from an alignment.
    For + strand: gets softclipped region at 5' end of read
    For - strand: gets softclipped region at 3' end of read
    
    Args:
        read: A pysam.AlignedSegment object
    
    Returns:
        str: Softclipped sequence or empty string if none exists
    """
    # Check if the read is unmapped
    if read.is_unmapped:
        return ""
    
    # Get the CIGAR operations
    cigar = read.cigartuples
    if not cigar:
        return ""
    
    # Determine if read is on reverse strand
    is_reverse = read.is_reverse
    
    # For + strand (forward): get softclip at 5' end (first operation)
    # For - strand (reverse): get softclip at 3' end (last operation)
    if is_reverse:
        # We want the last operation for reverse strand
        last_op = cigar[-1]
        if last_op[0] == 4:  # 4 is the CIGAR code for softclip
            # Get softclipped region at 3' end (last part of sequence)
            soft_clip_length = last_op[1]
            return read.query_sequence[-soft_clip_length:]
    else:
        # We want the first operation for forward strand
        first_op = cigar[0]
        if first_op[0] == 4:  # 4 is the CIGAR code for softclip
            # Get softclipped region at 5' end (first part of sequence)
            soft_clip_length = first_op[1]
            return read.query_sequence[:soft_clip_length]
    
    # No softclipped region found based on criteria
    return ""

# %% ../nbs/02_bam_processing.ipynb 10
def process_bam_file(
    config: BarcodeExtractorConfig,
    bam_file: str
) -> ExtractionStatistics:
    """Process a BAM file to extract barcodes.
    
    Args:
        config: Barcode extractor configuration
        bam_file: Path to the input BAM file
    
    Returns:
        Statistics from the extraction process
    """
    logger = config.logger
    
    # Validate BAM file
    if not os.path.exists(bam_file):
        raise FileNotFoundError(f"BAM file not found: {bam_file}")
    
    # Check if BAM file is sorted and indexed
    try:
        # Try to open the index file
        pysam.AlignmentFile(bam_file, "rb").check_index()
        is_indexed = True
    except (ValueError, IOError):
        logger.warning(f"BAM file is not indexed: {bam_file}")
        logger.info("Sorting and indexing BAM file...")
        BamUtils.sort_and_index(bam_file)
        is_indexed = True
    
    # Count the total number of reads
    total_reads = BamUtils.get_read_count(bam_file)
    logger.info(f"BAM file: {bam_file} ({total_reads} reads)")
    
    # Prepare output categories
    single_barcode_mode = len(config.barcodes) == 1 or all(b.location.value == "UNK" for b in config.barcodes)
    categories = prepare_bam_categories(config.barcodes, single_barcode_mode)
    logger.info(f"Output categories: {categories}")
    
    # Initialize statistics
    stats = ExtractionStatistics()
    stats.total_reads = total_reads
    
    # Open the input BAM file
    bamfile = pysam.AlignmentFile(bam_file, "rb")
    
    # Initialize output BAM files only if we're writing output
    output_files = {}
    if config.write_output_files:
        for category in categories:
            output_path = get_output_path(config.output_prefix, config.output_dir, category)
            output_files[category] = pysam.AlignmentFile(
                output_path, "wb", template=bamfile
            )
    
    # Track processed reads to avoid duplicates
    read_classifications = {}
    
    try:
        # First pass: classify reads by barcode
        for read in tqdm(bamfile, desc="Classifying reads", total=total_reads):
            # Skip if we've already processed this read
            if read.query_name in read_classifications:
                continue
            
            # Get the read sequence
            if config.search_softclipped:
                sequence = extract_softclipped_region(read)
            else:
                sequence = read.query_sequence
            
            if not sequence:
                continue
            
            # Search for barcodes
            match, category = classify_read(sequence, config.barcodes, config.max_mismatches, single_barcode_mode)
            
            # Update statistics and classification
            if match:
                stats.update_barcode_match(match, category)
                read_classifications[read.query_name] = category
        
        logger.info(f"First pass complete: classified {len(read_classifications)} reads")
        
        # Only perform second pass if writing output files
        if config.write_output_files:
            # Reset for second pass
            bamfile.close()
            bamfile = pysam.AlignmentFile(bam_file, "rb")
            
            # Second pass: write reads to output files
            for read in tqdm(bamfile, desc="Writing reads", total=total_reads):
                category = read_classifications.get(read.query_name, "noBarcode")
                
                # Write to output file
                if category in output_files:
                    output_files[category].write(read)
            
            # Close and sort output files
            for f in output_files.values():
                f.close()
            
            # Sort and index all output files
            for category in categories:
                file_path = get_output_path(config.output_prefix, config.output_dir, category)
                logger.info(f"Sorting and indexing {file_path}")
                BamUtils.sort_and_index(file_path)
    
    finally:
        # Close all file handles
        bamfile.close()
        for f in output_files.values():
            f.close()
    
    # Save statistics
    if config.write_output_files:
        save_statistics(stats, config.output_prefix, config.output_dir)
    else:
        # When not writing sequence files, still write statistics
        # (Optionally create output directory if it doesn't exist)
        os.makedirs(config.output_dir, exist_ok=True)
        save_statistics(stats, config.output_prefix, config.output_dir)
    
    return stats

# %% ../nbs/02_bam_processing.ipynb 12
def prepare_bam_categories(barcodes: List[BarcodeConfig], single_barcode_mode: bool) -> List[str]:
    """Prepare output categories based on barcodes.
    
    Args:
        barcodes: List of barcode configurations
        single_barcode_mode: Whether we're in single barcode mode
    
    Returns:
        List of category names
    """
    categories = []
    
    if single_barcode_mode:
        # Single barcode mode (either one barcode or multiple without specific locations)
        categories.extend(["barcode_orientFR", "barcode_orientRC"])
    else:
        # Multiple barcodes with specific locations (5' and/or 3')
        for barcode in barcodes:
            if barcode.location.value in ["5", "3"]:
                categories.extend([
                    f"barcode{barcode.location.value}_orientFR",
                    f"barcode{barcode.location.value}_orientRC"
                ])
    
    # Add no barcode category
    categories.append("noBarcode")
    
    return categories

# %% ../nbs/02_bam_processing.ipynb 13
def classify_read(
    sequence: str,
    barcodes: List[BarcodeConfig],
    max_mismatches: int,
    single_barcode_mode: bool
) -> Tuple[Optional[BarcodeMatch], str]:
    """Classify a read sequence based on barcode matches.
    
    Args:
        sequence: Read sequence to classify
        barcodes: List of barcode configurations
        max_mismatches: Maximum number of mismatches allowed
        single_barcode_mode: Whether we're in single barcode mode
        
    Returns:
        Tuple of (best_match, category)
    """
    sequence = sequence.upper()
    match, original_category = classify_read_by_first_match(
        sequence=sequence,
        barcodes=barcodes,
        max_mismatches=max_mismatches
    )
    
    # Adjust category based on single barcode mode or specific location mode
    if match:
        if single_barcode_mode:
            # For single barcode mode, use simpler categories
            if match.orientation == OrientationType.FORWARD:
                return match, "barcode_orientFR"
            else:  # REVERSE_COMPLEMENT
                return match, "barcode_orientRC"
        else:
            # For multiple barcodes with locations, use the location in the category
            location = match.barcode.location.value
            if location in ["5", "3"]:
                orientation = match.orientation.value
                return match, f"barcode{location}_orient{orientation}"
    
    return match, "noBarcode"

# %% ../nbs/02_bam_processing.ipynb 14
def get_output_path(output_prefix: str, output_dir: str, category: str) -> str:
    """Get the output path for a category.
    
    Args:
        output_prefix: Prefix for output files
        output_dir: Directory for output files
        category: Category name
        
    Returns:
        Path to the output BAM file
    """
    filename = f"{output_prefix}_{category}.bam"
    return os.path.join(output_dir, filename)

# %% ../nbs/02_bam_processing.ipynb 15
def save_statistics(stats: ExtractionStatistics, output_prefix: str, output_dir: str) -> None:
    """Save extraction statistics to files.
    
    Args:
        stats: Extraction statistics
        output_prefix: Prefix for output files
        output_dir: Directory for output files
    """
    # Save as JSON
    json_path = os.path.join(output_dir, f"{output_prefix}_extraction_stats.json")
    stats.save_json(json_path)
    
    # Save as TSV
    tsv_path = os.path.join(output_dir, f"{output_prefix}_extraction_stats.tsv")
    stats.save_tsv(tsv_path)
