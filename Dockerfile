FROM continuumio/miniconda3:latest

# Set working directory
WORKDIR /app

# Copy the package source code
COPY . /app/

# Set conda to be more efficient
# Create conda environment with mamba for faster installation
# Install mamba first as a faster conda alternative
RUN conda install -y -c conda-forge -c bioconda biopython pandas tqdm
RUN conda install -y -c conda-forge -c bioconda fastcore regex pyyaml
RUN conda install -y -c conda-forge -c bioconda samtools pysam 
RUN pip install -e . -vv

# Test the installation
RUN python -c "import BarcodeSeqKit"

# Verify the console script is properly installed
RUN which barcodeseqkit

# Set the entrypoint to use the console script
ENTRYPOINT ["barcodeseqkit"]