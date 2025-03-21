BarcodeSeqKit
================

<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

### Key Features

- **Simple yet powerful**: Extract barcodes from BAM or FASTQ files with
  minimal code
- **Support for both file types**: Process BAM files (including
  softclipped regions) and FASTQ files (including paired-end data)
- **Flexible barcode options**: Use single barcodes or specific 5’/3’
  combinations
- **Orientation detection**: Identify barcodes in both forward and
  reverse complement orientations
- **Fuzzy matching**: Configure allowable mismatches for barcode
  detection
- **Specialized functions**: Search in softclipped regions of BAM
  alignments or both reads in paired FASTQ data
- **Detailed statistics**: Get comprehensive reports on barcode matches
  and distribution

## Installation

You can install BarcodeSeqKit using pip:

``` bash
pip install barcodeseqkit
```

Or directly from the GitHub repository:

``` bash
pip install git+https://github.com/username/BarcodeSeqKit.git
```

### Quick Start

Let’s dive right in with some common use cases!

### Command-line Usage

BarcodeSeqKit provides a simple command-line interface that makes it
easy to extract barcodes without writing any code.

#### Extract a Single Barcode

``` bash
barcodeseqkit --bam tests/test.bam \
              --barcode CTGACTCCTTAAGGGCC \
              --output-prefix single_barcode \
              --output-dir results
```

This command extracts reads containing the specified barcode (in either
forward or reverse complement orientation) and creates: -
`results/single_barcode_barcode_orientFR.bam`: Forward orientation
matches - `results/single_barcode_barcode_orientRC.bam`: Reverse
complement matches - `results/single_barcode_extraction_stats.json`:
Detailed statistics in JSON format -
`results/single_barcode_extraction_stats.tsv`: Detailed statistics in
TSV format

#### Extract 5’ and 3’ Barcodes

``` bash
barcodeseqkit --bam tests/test.bam \
              --barcode5 CTGACTCCTTAAGGGCC \
              --barcode3 TAACTGAGGCCGGC \
              --output-prefix dual_barcode \
              --output-dir results
```

This creates separate files for each barcode and orientation
combination: - `results/dual_barcode_barcode5_orientFR.bam` -
`results/dual_barcode_barcode5_orientRC.bam` -
`results/dual_barcode_barcode3_orientFR.bam` -
`results/dual_barcode_barcode3_orientRC.bam`

#### Process Paired FASTQ Files

``` bash
barcodeseqkit --fastq1 tests/test.1.fastq.gz \
              --fastq2 tests/test.2.fastq.gz \
              --barcode5 CTGACTCCTTAAGGGCC \
              --output-prefix fastq_extraction \
              --search-both-reads
```

This processes paired FASTQ files and creates output FASTQ files for
each barcode category.

### Python API Usage

BarcodeSeqKit’s Python API is designed to be intuitive and
straightforward:

``` python
from BarcodeSeqKit.core import BarcodeConfig, BarcodeLocationType, BarcodeExtractorConfig
from BarcodeSeqKit.bam_processing import process_bam_file

# Define barcodes
barcodes = [
    BarcodeConfig(
        sequence="TAACTGAGGCCGGC",
        location=BarcodeLocationType.THREE_PRIME,
        name="3prime"
    ),
    BarcodeConfig(
        sequence="CTGACTCCTTAAGGGCC",
        location=BarcodeLocationType.FIVE_PRIME,
        name="5prime"
    )
]

# Create configuration
config = BarcodeExtractorConfig(
    barcodes=barcodes,
    output_prefix="my_extraction",
    output_dir="./results",
    max_mismatches=0,
    search_softclipped=True,
    verbose=True
)

# Process BAM file
stats = process_bam_file(config, "tests/test.bam")

# Report results
print(f"Processed {stats.total_reads} reads")
print(f"Found {stats.total_barcode_matches} barcode matches")
```

or FASTQ files:

``` python
from BarcodeSeqKit.fastq_processing import process_fastq_files

# Use the same config as above
fastq_files = ["tests/test.1.fastq.gz", "tests/test.2.fastq.gz"]
stats = process_fastq_files(
    config=config,
    fastq_files=fastq_files,
    compress_output=True,
    search_both_reads=True
)
```

``` python
## Key Concepts
```

### Barcode Types

BarcodeSeqKit supports three types of barcode configurations:

1.  **Generic barcodes**: Use these when you just want to find a
    specific sequence regardless of location
2.  **5’ barcodes**: Use these when the barcode is expected at the 5’
    end of the sequence
3.  **3’ barcodes**: Use these when the barcode is expected at the 3’
    end of the sequence

## Barcode Orientations

For each barcode, BarcodeSeqKit tracks two possible orientations:

- **Forward (FR)**: The barcode appears in its specified sequence
- **Reverse Complement (RC)**: The barcode appears as its reverse
  complement

## Softclipped Regions

When working with BAM files, the `--search-softclipped` option examines
only the softclipped portions of reads:

- For forward strand reads (+): Examines the 5’ softclipped region
- For reverse strand reads (-): Examines the 3’ softclipped region

This is especially useful for splice leader sequences in trypanosomatids
or where barcodes are clipped during alignment.

## Advanced Options

### Command-Line Arguments

BarcodeSeqKit offers a range of options to customize your extraction:

| Option                 | Description                                           |
|------------------------|-------------------------------------------------------|
| `--max-mismatches N`   | Allow up to N mismatches in barcode detection         |
| `--search-softclipped` | Search in softclipped regions (BAM only)              |
| `--search-both-reads`  | Look for barcodes in both reads of paired FASTQ files |
| `--no-compress`        | Disable compression for FASTQ output files            |
| `--verbose`            | Enable detailed logging                               |

For a complete list, run `barcodeseqkit --help`.

### Barcode Configuration Files

For complex projects with multiple barcodes, you can use a YAML
configuration file:

``` yaml
barcodes:
  - sequence: CTGACTCCTTAAGGGCC
    location: 5
    name: 5prime
    description: 5' barcode for experiment X
  - sequence: TAACTGAGGCCGGC
    location: 3
    name: 3prime
    description: 3' barcode for experiment X
```

Then use it with:

``` bash
barcodeseqkit --bam test.bam --barcode-config my_barcodes.yaml --output-prefix config_extraction
```

## Output Files and Statistics

BarcodeSeqKit generates:

1.  **Categorized output files**: BAM or FASTQ files containing reads
    matching specific barcode/orientation combinations
2.  **Statistics in JSON format**: Detailed machine-readable statistics
3.  **Statistics in TSV format**: Human-readable tabular statistics

The statistics include: - Total number of reads processed - Total
barcode matches found - Match counts by barcode type - Match counts by
orientation - Match counts by category - Overall match rate

BarcodeSeqKit has a clean, modular design:

1.  **Core** (`00_core.ipynb`): Data structures and configuration
2.  **Sequence Utilities** (`01_sequence_utils.ipynb`): Barcode
    detection algorithms
3.  **BAM Processing** (`02_bam_processing.ipynb`): BAM file handling
4.  **FASTQ Processing** (`03_fastq_processing.ipynb`): FASTQ file
    handling
5.  **Command-Line Interface** (`04_cli.ipynb`): Argument parsing and
    execution

## Real-World Example

Let’s walk through a practical example of extracting barcodes from the
test data included with BarcodeSeqKit:

``` python
from BarcodeSeqKit.core import BarcodeConfig, BarcodeLocationType, BarcodeExtractorConfig
from BarcodeSeqKit.bam_processing import process_bam_file
import os

# Define barcodes that we know are in the test data
barcodes = [
    BarcodeConfig(
        sequence="TAACTGAGGCCGGC",
        location=BarcodeLocationType.THREE_PRIME,
        name="3prime"
    ),
    BarcodeConfig(
        sequence="CTGACTCCTTAAGGGCC",
        location=BarcodeLocationType.FIVE_PRIME,
        name="5prime"
    )
]

# Create configuration
output_dir = "../tests/index_api"
os.makedirs(output_dir, exist_ok=True)

config = BarcodeExtractorConfig(
    barcodes=barcodes,
    output_prefix="example_run",
    output_dir=output_dir,
    max_mismatches=0,
    search_softclipped=True,
    verbose=True
)

# Process the BAM file (if it exists)
test_bam = "../tests/test.bam"
if os.path.exists(test_bam):
    print(f"Processing {test_bam}")
    stats = process_bam_file(config, test_bam)
    
    # Print summary statistics
    print(f"\nResults summary:")
    print(f"Total reads: {stats.total_reads}")
    print(f"Total barcode matches: {stats.total_barcode_matches}")
    
    if stats.total_reads > 0:
        match_rate = (stats.total_barcode_matches / stats.total_reads) * 100
        print(f"Match rate: {match_rate:.2f}%")
    
    # Print barcode-specific statistics
    for barcode_name, count in stats.matches_by_barcode.items():
        print(f"  {barcode_name}: {count} matches")
    
    # Print orientation-specific statistics
    for orientation, count in stats.matches_by_orientation.items():
        print(f"  Orientation {orientation}: {count} matches")
else:
    print(f"Test file not found: {test_bam}")
```

    2025-03-17 12:19:54,956 - BarcodeSeqKit - INFO - BAM file: ../tests/test.bam (498 reads)
    2025-03-17 12:19:54,958 - BarcodeSeqKit - INFO - Output categories: ['barcode3_orientFR', 'barcode3_orientRC', 'barcode5_orientFR', 'barcode5_orientRC', 'noBarcode']

    Processing ../tests/test.bam

    Classifying reads:   0%|          | 0/498 [00:00<?, ?it/s]

    2025-03-17 12:19:55,013 - BarcodeSeqKit - INFO - First pass complete: classified 18 reads

    Writing reads:   0%|          | 0/498 [00:00<?, ?it/s]

    2025-03-17 12:19:55,049 - BarcodeSeqKit - INFO - Sorting and indexing ../tests/index_api/example_run_barcode3_orientFR.bam
    2025-03-17 12:19:55,081 - BarcodeSeqKit - INFO - Sorting and indexing ../tests/index_api/example_run_barcode3_orientRC.bam
    2025-03-17 12:19:55,095 - BarcodeSeqKit - INFO - Sorting and indexing ../tests/index_api/example_run_barcode5_orientFR.bam
    2025-03-17 12:19:55,106 - BarcodeSeqKit - INFO - Sorting and indexing ../tests/index_api/example_run_barcode5_orientRC.bam
    2025-03-17 12:19:55,136 - BarcodeSeqKit - INFO - Sorting and indexing ../tests/index_api/example_run_noBarcode.bam


    Results summary:
    Total reads: 498
    Total barcode matches: 18
    Match rate: 3.61%
      5prime: 10 matches
      3prime: 8 matches
      Orientation FR: 10 matches
      Orientation RC: 8 matches

``` python
!barcodeseqkit --bam ../tests/test.bam \
              --barcode5 CTGACTCCTTAAGGGCC \
              --barcode3 TAACTGAGGCCGGC \
              --output-prefix dual_barcode \
              --output-dir ../tests/index_cli
```

    Input BAM file: ../tests/test.bam
    Using 5' barcode with sequence: CTGACTCCTTAAGGGCC
    Using 3' barcode with sequence: TAACTGAGGCCGGC
    Saved configuration to ../tests/index_cli/dual_barcode_config.yaml
    2025-03-17 12:18:29,756 - BarcodeSeqKit - INFO - BAM file: ../tests/test.bam (498 reads)
    2025-03-17 12:18:29,756 - BarcodeSeqKit - INFO - Output categories: ['barcode5_orientFR', 'barcode5_orientRC', 'barcode3_orientFR', 'barcode3_orientRC', 'noBarcode']
    Classifying reads: 100%|███████████████████| 498/498 [00:00<00:00, 58040.55it/s]
    2025-03-17 12:18:29,810 - BarcodeSeqKit - INFO - First pass complete: classified 18 reads
    Writing reads: 100%|██████████████████████| 498/498 [00:00<00:00, 230344.44it/s]
    2025-03-17 12:18:29,816 - BarcodeSeqKit - INFO - Sorting and indexing ../tests/index_cli/dual_barcode_barcode5_orientFR.bam
    2025-03-17 12:18:29,844 - BarcodeSeqKit - INFO - Sorting and indexing ../tests/index_cli/dual_barcode_barcode5_orientRC.bam
    2025-03-17 12:18:29,856 - BarcodeSeqKit - INFO - Sorting and indexing ../tests/index_cli/dual_barcode_barcode3_orientFR.bam
    2025-03-17 12:18:29,882 - BarcodeSeqKit - INFO - Sorting and indexing ../tests/index_cli/dual_barcode_barcode3_orientRC.bam
    2025-03-17 12:18:29,894 - BarcodeSeqKit - INFO - Sorting and indexing ../tests/index_cli/dual_barcode_noBarcode.bam
    Extraction complete

## Conclusion

BarcodeSeqKit provides a streamlined, user-friendly approach to barcode
extraction from sequencing data. With its intuitive interface and
flexible options, it’s suitable for a wide range of applications, from
simple barcode detection to complex multi-barcode analyses.

Whether you’re working with BAM files, FASTQ files, single barcodes, or
multiple barcodes with specific locations, BarcodeSeqKit offers a
straightforward solution for your barcode extraction needs.

For detailed API documentation, check out the module-specific
notebooks: - [Core Data Structures](00_core.ipynb) - [Sequence
Utilities](01_sequence_utils.ipynb) - [BAM
Processing](02_bam_processing.ipynb) - [FASTQ
Processing](03_fastq_processing.ipynb) - [Command-Line
Interface](04_cli.ipynb)
