"""Core abstractions for barcode extraction from sequencing data"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['OrientationType', 'BarcodeLocationType', 'BarcodeConfig', 'BarcodeMatch', 'ExtractionStatistics', 'BarcodeExtractor',
           'SequenceProcessor', 'ExtractorConfig', 'FileFormat', 'ExtractorFactory']

# %% ../nbs/00_core.ipynb 4
import os
import re
import sys
import gzip
import json
import enum
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Optional, Union, Iterator, Any
from Bio.Seq import Seq

# %% ../nbs/00_core.ipynb 6
class OrientationType(enum.Enum):
    """Orientation types for barcode sequences."""
    FORWARD = "FR"
    REVERSE_COMPLEMENT = "RC"
    ANY = "ANY"

# %% ../nbs/00_core.ipynb 7
class BarcodeLocationType(enum.Enum):
    """Location types for barcodes."""
    FIVE_PRIME = "5"
    THREE_PRIME = "3"
    UNKNOWN = "UNK"

# %% ../nbs/00_core.ipynb 8
@dataclass
class BarcodeConfig:
    """Configuration for a barcode sequence."""
    sequence: str
    location: BarcodeLocationType = BarcodeLocationType.UNKNOWN
    name: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        # Clean the sequence and ensure uppercase
        self.sequence = self.sequence.strip().upper()
        # If no name is provided, use the sequence as the name
        if self.name is None:
            self.name = self.sequence
    
    @property
    def reverse_complement(self) -> str:
        """Return the reverse complement of the barcode sequence."""
        return str(Seq(self.sequence).reverse_complement())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the barcode configuration to a dictionary."""
        return {
            "sequence": self.sequence,
            "location": self.location.value,
            "name": self.name,
            "description": self.description,
            "reverse_complement": self.reverse_complement
        }

# %% ../nbs/00_core.ipynb 9
@dataclass
class BarcodeMatch:
    """Represents a match of a barcode in a sequence."""
    barcode: BarcodeConfig
    orientation: OrientationType
    position: int
    sequence: str
    
    def __str__(self) -> str:
        """String representation of the barcode match."""
        return f"{self.barcode.name} ({self.orientation.value}) at position {self.position}"

# %% ../nbs/00_core.ipynb 11
@dataclass
class ExtractionStatistics:
    """Statistics collected during barcode extraction."""
    total_reads: int = 0
    total_barcode_matches: int = 0
    matches_by_barcode: Dict[str, int] = field(default_factory=dict)
    matches_by_orientation: Dict[str, int] = field(default_factory=dict)
    matches_by_category: Dict[str, int] = field(default_factory=dict)  # New field for category stats
    no_barcode_count: int = 0
    
    def update_barcode_match(self, barcode_match: BarcodeMatch, category: Optional[str] = None) -> None:
        """Update statistics based on a barcode match.
        
        Args:
            barcode_match: The barcode match
            category: The category (e.g., 'barcode5_orientFR'). If None, will be derived from the match.
        """
        self.total_barcode_matches += 1
        
        # Update matches by barcode
        barcode_name = barcode_match.barcode.name
        if barcode_name not in self.matches_by_barcode:
            self.matches_by_barcode[barcode_name] = 0
        self.matches_by_barcode[barcode_name] += 1
        
        # Update matches by orientation
        orientation = barcode_match.orientation.value
        if orientation not in self.matches_by_orientation:
            self.matches_by_orientation[orientation] = 0
        self.matches_by_orientation[orientation] += 1
        
        # Derive category if not provided
        if category is None:
            # Try to derive a reasonable category
            location = barcode_match.barcode.location.value
            if location in ["5", "3"]:
                category = f"barcode{location}_orient{orientation}"
            else:
                category = f"barcode_orient{orientation}"
        
        # Update matches by category
        if category not in self.matches_by_category:
            self.matches_by_category[category] = 0
        self.matches_by_category[category] += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the statistics to a dictionary."""
        return {
            "total_reads": self.total_reads,
            "total_barcode_matches": self.total_barcode_matches,
            "matches_by_barcode": self.matches_by_barcode,
            "matches_by_orientation": self.matches_by_orientation,
            "matches_by_category": self.matches_by_category,
            "no_barcode_count": self.no_barcode_count,
            "match_rate": (self.total_barcode_matches / self.total_reads) if self.total_reads > 0 else 0
        }
    
    def save_json(self, output_path: str) -> None:
        """Save the statistics to a JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def save_tsv(self, output_path: str) -> None:
        """Save the statistics to a TSV file."""
        with open(output_path, 'w') as f:
            # Write header
            f.write("Metric\tValue\n")
            
            # Write overall statistics
            stats_dict = self.to_dict()
            f.write(f"TotalReads\t{stats_dict['total_reads']}\n")
            f.write(f"TotalBarcodeMatches\t{stats_dict['total_barcode_matches']}\n")
            f.write(f"NoBarcodeCount\t{stats_dict['no_barcode_count']}\n")
            f.write(f"MatchRate\t{stats_dict['match_rate']:.4f}\n")
            
            # Write barcode-specific statistics
            f.write("\nBarcode\tCount\n")
            for barcode, count in stats_dict['matches_by_barcode'].items():
                f.write(f"{barcode}\t{count}\n")
            
            # Write orientation-specific statistics
            f.write("\nOrientation\tCount\n")
            for orientation, count in stats_dict['matches_by_orientation'].items():
                f.write(f"{orientation}\t{count}\n")
            
            # Write category-specific statistics
            f.write("\nCategory\tCount\n")
            for category, count in stats_dict['matches_by_category'].items():
                f.write(f"{category}\t{count}\n")

# %% ../nbs/00_core.ipynb 12
class BarcodeExtractor(ABC):
    """Abstract base class for barcode extraction from sequencing data."""
    
    def __init__(
        self, 
        barcodes: List[BarcodeConfig],
        output_prefix: str,
        output_dir: Optional[str] = None,
        merge_orientations: bool = False,
        keep_unmatched: bool = True,
        verbose: bool = False,
        log_file: Optional[str] = None
    ):
        self.barcodes = barcodes
        self.output_prefix = output_prefix
        self.output_dir = output_dir if output_dir else os.getcwd()
        self.merge_orientations = merge_orientations
        self.keep_unmatched = keep_unmatched
        self.verbose = verbose
        self.statistics = ExtractionStatistics()
        
        # Set up logging
        self.logger = self._setup_logging(log_file)
        
        # Validate and prepare barcodes
        self._validate_barcodes()
        
        # Prepare output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _setup_logging(self, log_file: Optional[str]) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger("BarcodeSeqKit")
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler (if requested)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _validate_barcodes(self) -> None:
        """Validate barcode configurations."""
        if not self.barcodes:
            raise ValueError("At least one barcode must be provided")
        
        # Check for duplicate sequences
        sequences = [barcode.sequence for barcode in self.barcodes]
        if len(sequences) != len(set(sequences)):
            self.logger.warning("Duplicate barcode sequences detected")
        
        # Check for invalid sequences
        valid_bases = set("ACGTN")
        for barcode in self.barcodes:
            if not all(base in valid_bases for base in barcode.sequence):
                raise ValueError(f"Invalid barcode sequence: {barcode.sequence}")
    
    @abstractmethod
    def extract(self) -> ExtractionStatistics:
        """Extract barcodes from the input data."""
        pass
    
    @abstractmethod
    def _find_barcode_matches(self, sequence: str) -> List[BarcodeMatch]:
        """Find barcode matches in a sequence."""
        pass
    
    def _get_output_path(self, barcode_name: str, orientation: OrientationType, suffix: str) -> str:
        """Generate an output file path based on barcode and orientation."""
        if barcode_name == "noBarcode":
            filename = f"{self.output_prefix}_{barcode_name}{suffix}"
        else:
            filename = f"{self.output_prefix}_barcode{barcode_name}_orient{orientation.value}{suffix}"
        
        return os.path.join(self.output_dir, filename)
    
    def _get_combined_output_path(self, barcode_name: str, suffix: str) -> str:
        """Generate a combined output file path for a barcode."""
        filename = f"{self.output_prefix}_combined_barcode{barcode_name}{suffix}"
        return os.path.join(self.output_dir, filename)
    
    def save_statistics(self) -> None:
        """Save extraction statistics to files."""
        # Save as JSON
        json_path = os.path.join(self.output_dir, f"{self.output_prefix}_extraction_stats.json")
        self.statistics.save_json(json_path)
        
        # Save as TSV
        tsv_path = os.path.join(self.output_dir, f"{self.output_prefix}_extraction_stats.tsv")
        self.statistics.save_tsv(tsv_path)
        
        self.logger.info(f"Statistics saved to {json_path} and {tsv_path}")

# %% ../nbs/00_core.ipynb 14
class SequenceProcessor:
    """Utility class for processing sequences and finding barcode matches."""
    
    @staticmethod
    def find_barcode_matches(sequence: str, barcodes: List[BarcodeConfig]) -> List[BarcodeMatch]:
        """Find all barcode matches in a sequence.
        
        Args:
            sequence: The sequence to search in
            barcodes: List of barcode configurations to search for
            
        Returns:
            List of BarcodeMatch objects representing the matches found
        """
        matches = []
        
        for barcode in barcodes:
            # Search for forward sequence
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
        
        return matches

# %% ../nbs/00_core.ipynb 16
@dataclass
class ExtractorConfig:
    """Configuration for the barcode extractor."""
    barcodes: List[BarcodeConfig]
    output_prefix: str
    output_dir: str = "."
    merge_orientations: bool = False
    keep_unmatched: bool = True
    verbose: bool = False
    log_file: Optional[str] = None
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ExtractorConfig':
        """Create a configuration from a dictionary."""
        # Extract barcode configurations
        barcode_configs = []
        for barcode_dict in config_dict.get("barcodes", []):
            location = BarcodeLocationType(barcode_dict.get("location", "UNK"))
            barcode_configs.append(BarcodeConfig(
                sequence=barcode_dict["sequence"],
                location=location,
                name=barcode_dict.get("name"),
                description=barcode_dict.get("description")
            ))
        
        # Create and return the configuration
        return cls(
            barcodes=barcode_configs,
            output_prefix=config_dict["output_prefix"],
            output_dir=config_dict.get("output_dir", "."),
            merge_orientations=config_dict.get("merge_orientations", False),
            keep_unmatched=config_dict.get("keep_unmatched", True),
            verbose=config_dict.get("verbose", False),
            log_file=config_dict.get("log_file")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {
            "barcodes": [barcode.to_dict() for barcode in self.barcodes],
            "output_prefix": self.output_prefix,
            "output_dir": self.output_dir,
            "merge_orientations": self.merge_orientations,
            "keep_unmatched": self.keep_unmatched,
            "verbose": self.verbose,
            "log_file": self.log_file
        }
    
    def save_yaml(self, output_path: str) -> None:
        """Save the configuration to a YAML file."""
        import yaml
        with open(output_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
    
    @classmethod
    def load_yaml(cls, input_path: str) -> 'ExtractorConfig':
        """Load configuration from a YAML file."""
        import yaml
        with open(input_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)

# %% ../nbs/00_core.ipynb 18
class FileFormat(enum.Enum):
    """Supported file formats."""
    BAM = "BAM"
    FASTQ = "FASTQ"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def detect_format(cls, file_path: str) -> 'FileFormat':
        """Detect the format of a file based on its extension."""
        lower_path = file_path.lower()
        if lower_path.endswith('.bam'):
            return cls.BAM
        elif any(lower_path.endswith(ext) for ext in ['.fastq', '.fq', '.fastq.gz', '.fq.gz']):
            return cls.FASTQ
        else:
            return cls.UNKNOWN

# %% ../nbs/00_core.ipynb 20
class FileFormat(enum.Enum):
    """Supported file formats."""
    BAM = "BAM"
    FASTQ = "FASTQ"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def detect_format(cls, file_path: str) -> 'FileFormat':
        """Detect the format of a file based on its extension."""
        lower_path = file_path.lower()
        if lower_path.endswith('.bam'):
            return cls.BAM
        elif any(lower_path.endswith(ext) for ext in ['.fastq', '.fq', '.fastq.gz', '.fq.gz']):
            return cls.FASTQ
        else:
            return cls.UNKNOWN

# %% ../nbs/00_core.ipynb 21
class ExtractorFactory:
    """Factory for creating barcode extractors based on file format."""
    
    @staticmethod
    def create_extractor(
        config: ExtractorConfig,
        input_files: Union[str, List[str]]
    ) -> BarcodeExtractor:
        """Create a barcode extractor based on the input file format.
        
        Args:
            config: Extractor configuration
            input_files: Path to input file(s)
            
        Returns:
            An appropriate BarcodeExtractor implementation
            
        Raises:
            ValueError: If the file format is unsupported or inconsistent
        """
        # Handle single file input
        if isinstance(input_files, str):
            input_files = [input_files]
        
        # Detect file format
        formats = [FileFormat.detect_format(f) for f in input_files]
        
        # Check for consistent formats
        if len(set(formats)) > 1:
            raise ValueError("Mixed file formats are not supported")
        
        format_type = formats[0]
        
        # Import the appropriate extractor
        if format_type == FileFormat.BAM:
            # Importing here to avoid circular imports
            from BarcodeSeqKit.bam_processing import BamExtractor
            return BamExtractor(
                barcodes=config.barcodes,
                output_prefix=config.output_prefix,
                output_dir=config.output_dir,
                merge_orientations=config.merge_orientations,
                keep_unmatched=config.keep_unmatched,
                verbose=config.verbose,
                log_file=config.log_file,
                bam_file=input_files[0]
            )
        elif format_type == FileFormat.FASTQ:
            # Importing here to avoid circular imports
            from BarcodeSeqKit.fastq_processing import FastqExtractor
            
            # Check if we have paired files
            if len(input_files) == 1:
                # Single path provided, check if it's a directory
                if os.path.isdir(input_files[0]):
                    from BarcodeSeqKit.fastq_processing import FastqHandler
                    # Find paired files in the directory
                    r1_path, r2_path = FastqHandler.find_fastq_pairs(input_files[0])
                    fastq_files = [r1_path, r2_path]
                else:
                    # Single FASTQ file
                    fastq_files = input_files
            elif len(input_files) == 2:
                # Paired FASTQ files
                fastq_files = input_files
            else:
                raise ValueError("For FASTQ input, provide either a directory or exactly two files")
            
            return FastqExtractor(
                barcodes=config.barcodes,
                output_prefix=config.output_prefix,
                output_dir=config.output_dir,
                merge_orientations=config.merge_orientations,
                keep_unmatched=config.keep_unmatched,
                verbose=config.verbose,
                log_file=config.log_file,
                fastq_files=fastq_files
            )
        else:
            raise ValueError(f"Unsupported file format: {format_type}")
