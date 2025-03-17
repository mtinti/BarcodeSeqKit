"""Utilities for working with DNA/RNA sequences and barcode detection"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_sequence_utils.ipynb.

# %% auto 0
__all__ = ['reverse_complement', 'hamming_distance', 'find_barcode_matches', 'find_best_barcode_match',
           'classify_read_by_first_match', 'get_output_category', 'prepare_categories', 'extract_softclipped_region']

# %% ../nbs/01_sequence_utils.ipynb 4
import re
import regex  # For fuzzy matching
from typing import List, Dict, Tuple, Optional, Iterator, Set, Any, Union
from Bio.Seq import Seq
from .core import BarcodeConfig, BarcodeMatch, OrientationType, BarcodeLocationType

# %% ../nbs/01_sequence_utils.ipynb 6
def reverse_complement(sequence: str) -> str:
    """Return the reverse complement of a DNA sequence.
    
    Args:
        sequence: DNA sequence
        
    Returns:
        Reverse complement of the sequence
    """
    return str(Seq(sequence).reverse_complement())

# %% ../nbs/01_sequence_utils.ipynb 7
def hamming_distance(seq1: str, seq2: str) -> int:
    """Calculate the Hamming distance between two sequences.
    
    The sequences must be of the same length.
    
    Args:
        seq1: First sequence
        seq2: Second sequence
        
    Returns:
        Hamming distance (number of positions where the sequences differ)
        
    Raises:
        ValueError: If sequences have different lengths
    """
    if len(seq1) != len(seq2):
        raise ValueError("Sequences must have the same length")
    
    return sum(a != b for a, b in zip(seq1, seq2))

# %% ../nbs/01_sequence_utils.ipynb 9
def find_barcode_matches(
    sequence: str, 
    barcodes: List[BarcodeConfig],
    max_mismatches: int = 0
) -> List[BarcodeMatch]:
    """Find all barcode matches in a sequence.
    
    Args:
        sequence: The DNA/RNA sequence to search in
        barcodes: List of barcode configurations to search for
        max_mismatches: Maximum number of mismatches to allow
        
    Returns:
        List of BarcodeMatch objects representing the matches found
    """
    matches = []
    
    # Convert sequence to uppercase
    sequence = sequence.upper()
    
    for barcode in barcodes:
        # Search for forward sequence
        if max_mismatches == 0:
            # Exact matching with re
            forward_positions = [m.start() for m in re.finditer(barcode.sequence, sequence)]
            for pos in forward_positions:
                matches.append(BarcodeMatch(
                    barcode=barcode,
                    orientation=OrientationType.FORWARD,
                    position=pos,
                    sequence=sequence[pos:pos+len(barcode.sequence)]
                ))
            
            # Search for reverse complement sequence
            rc_seq = barcode.reverse_complement
            rc_positions = [m.start() for m in re.finditer(rc_seq, sequence)]
            for pos in rc_positions:
                matches.append(BarcodeMatch(
                    barcode=barcode,
                    orientation=OrientationType.REVERSE_COMPLEMENT,
                    position=pos,
                    sequence=sequence[pos:pos+len(rc_seq)]
                ))
        else:
            # Fuzzy matching with regex module
            # Forward orientation
            pattern = f"({barcode.sequence}){{e<={max_mismatches}}}"
            r = regex.compile(pattern)
            for match in r.finditer(sequence):
                matches.append(BarcodeMatch(
                    barcode=barcode,
                    orientation=OrientationType.FORWARD,
                    position=match.start(),
                    sequence=match.group()
                ))
            
            # Reverse complement orientation
            rc_pattern = f"({barcode.reverse_complement}){{e<={max_mismatches}}}"
            rc_r = regex.compile(rc_pattern)
            for match in rc_r.finditer(sequence):
                matches.append(BarcodeMatch(
                    barcode=barcode,
                    orientation=OrientationType.REVERSE_COMPLEMENT,
                    position=match.start(),
                    sequence=match.group()
                ))
    
    return matches

# %% ../nbs/01_sequence_utils.ipynb 10
def find_best_barcode_match(
    sequence: str, 
    barcodes: List[BarcodeConfig],
    max_mismatches: int = 1
) -> Optional[BarcodeMatch]:
    """Find the best matching barcode in a sequence.
    
    Args:
        sequence: The sequence to search in
        barcodes: List of barcode configurations to search for
        max_mismatches: Maximum number of mismatches to allow
        
    Returns:
        The best matching BarcodeMatch or None if no match found
    """
    best_match = None
    min_mismatches = max_mismatches + 1
    sequence = sequence.upper()
    
    for barcode in barcodes:
        # Check forward orientation with regex
        pattern = f"({barcode.sequence}){{e<={max_mismatches}}}"
        r = regex.compile(pattern)
        for match in r.finditer(sequence):
            # Get the fuzzy counts (substitutions, insertions, deletions)
            subs, ins, dels = match.fuzzy_counts
            total_mismatches = subs + ins + dels
            
            if total_mismatches < min_mismatches:
                min_mismatches = total_mismatches
                best_match = BarcodeMatch(
                    barcode=barcode,
                    orientation=OrientationType.FORWARD,
                    position=match.start(),
                    sequence=match.group()
                )
        
        # Check reverse complement orientation with regex
        rc_pattern = f"({barcode.reverse_complement}){{e<={max_mismatches}}}"
        rc_r = regex.compile(rc_pattern)
        for match in rc_r.finditer(sequence):
            # Get the fuzzy counts
            subs, ins, dels = match.fuzzy_counts
            total_mismatches = subs + ins + dels
            
            if total_mismatches < min_mismatches:
                min_mismatches = total_mismatches
                best_match = BarcodeMatch(
                    barcode=barcode,
                    orientation=OrientationType.REVERSE_COMPLEMENT,
                    position=match.start(),
                    sequence=match.group()
                )
    
    return best_match

# %% ../nbs/01_sequence_utils.ipynb 11
def classify_read_by_first_match(
    sequence: str, 
    barcodes: List[BarcodeConfig],
    max_mismatches: int = 0
) -> Tuple[Optional[BarcodeMatch], str]:
    """Classify a read based on the first barcode match found.
    
    This is an optimized version that stops after finding the first match,
    without evaluating all possible matches in the sequence.
    
    Args:
        sequence: The sequence to classify
        barcodes: List of barcode configurations to search for
        max_mismatches: Maximum number of mismatches to allow
        
    Returns:
        Tuple of (match, category)
        Category is one of: "barcode5_orientFR", "barcode5_orientRC", etc.
        or "noBarcode" if no match found
    """
    sequence = sequence.upper()
    
    # Determine if we're in single barcode mode or multiple barcode mode
    single_barcode_mode = len(barcodes) == 1 or all(b.location.value == "UNK" for b in barcodes)
    
    # Check each barcode in order
    for barcode in barcodes:
        # Check forward orientation first
        if max_mismatches == 0:
            # Exact match with re
            match = re.search(barcode.sequence, sequence)
            if match:
                barcode_match = BarcodeMatch(
                    barcode=barcode,
                    orientation=OrientationType.FORWARD,
                    position=match.start(),
                    sequence=match.group()
                )
                
                if single_barcode_mode:
                    return barcode_match, "barcode_orientFR"
                else:
                    location = barcode.location.value if barcode.location.value in ["5", "3"] else ""
                    return barcode_match, f"barcode{location}_orient{OrientationType.FORWARD.value}"
        else:
            # Fuzzy match with regex
            pattern = f"({barcode.sequence}){{e<={max_mismatches}}}"
            r = regex.compile(pattern)
            match = r.search(sequence)
            if match:
                barcode_match = BarcodeMatch(
                    barcode=barcode,
                    orientation=OrientationType.FORWARD,
                    position=match.start(),
                    sequence=match.group()
                )
                
                if single_barcode_mode:
                    return barcode_match, "barcode_orientFR"
                else:
                    location = barcode.location.value if barcode.location.value in ["5", "3"] else ""
                    return barcode_match, f"barcode{location}_orient{OrientationType.FORWARD.value}"
        
        # Check reverse complement orientation
        rc_seq = barcode.reverse_complement
        if max_mismatches == 0:
            # Exact match with re
            match = re.search(rc_seq, sequence)
            if match:
                barcode_match = BarcodeMatch(
                    barcode=barcode,
                    orientation=OrientationType.REVERSE_COMPLEMENT,
                    position=match.start(),
                    sequence=match.group()
                )
                
                if single_barcode_mode:
                    return barcode_match, "barcode_orientRC"
                else:
                    location = barcode.location.value if barcode.location.value in ["5", "3"] else ""
                    return barcode_match, f"barcode{location}_orient{OrientationType.REVERSE_COMPLEMENT.value}"
        else:
            # Fuzzy match with regex
            pattern = f"({rc_seq}){{e<={max_mismatches}}}"
            r = regex.compile(pattern)
            match = r.search(sequence)
            if match:
                barcode_match = BarcodeMatch(
                    barcode=barcode,
                    orientation=OrientationType.REVERSE_COMPLEMENT,
                    position=match.start(),
                    sequence=match.group()
                )
                
                if single_barcode_mode:
                    return barcode_match, "barcode_orientRC"
                else:
                    location = barcode.location.value if barcode.location.value in ["5", "3"] else ""
                    return barcode_match, f"barcode{location}_orient{OrientationType.REVERSE_COMPLEMENT.value}"
    
    # No match found
    return None, "noBarcode"

# %% ../nbs/01_sequence_utils.ipynb 13
def get_output_category(
    match: Optional[BarcodeMatch], 
    single_barcode_mode: bool = False
) -> str:
    """Get the output category for a barcode match.
    
    Args:
        match: Barcode match or None
        single_barcode_mode: Whether we're in single barcode mode
        
    Returns:
        Category string for output file naming
    """
    if match is None:
        return "noBarcode"
    
    if single_barcode_mode:
        return f"barcode_orient{match.orientation.value}"
    else:
        location = match.barcode.location.value
        if location in ["5", "3"]:
            return f"barcode{location}_orient{match.orientation.value}"
        else:
            return f"barcode_orient{match.orientation.value}"

def prepare_categories(barcodes: List[BarcodeConfig], keep_unmatched: bool = True) -> List[str]:
    """Prepare output categories based on barcodes.
    
    Args:
        barcodes: List of barcode configurations
        keep_unmatched: Whether to keep reads without barcodes
        
    Returns:
        List of category names
    """
    categories = []
    
    # Determine if we're in single barcode mode
    single_barcode_mode = len(barcodes) == 1 or all(b.location.value == "UNK" for b in barcodes)
    
    if single_barcode_mode:
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
    if keep_unmatched:
        categories.append("noBarcode")
    
    return categories

# %% ../nbs/01_sequence_utils.ipynb 15
def extract_softclipped_region(read) -> str:
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
