# unzip all
gunzip galahad-corpus-data/training-data/*/*.tsv.gz
# Could attempt to use shopt -s globstar
gunzip galahad-corpus-data/training-data/*/*/*.tsv.gz
# Remove comments
sed -i '/^#.*$/d' galahad-corpus-data/training-data/*/*.tsv
sed -i '/^#.*$/d' galahad-corpus-data/training-data/*/*/*.tsv
