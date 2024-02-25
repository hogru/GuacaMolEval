#!/bin/bash
# Sample script to evaluate molecules with Guacamol
# Current directory should contain the python scripts
# i.e. src/guacamoleval/

EVAL_SCRIPT="eval.py"
GENERATED_MOLECULES="../../data/generated/generated_smiles.csv"
REFERENCE_MOLECULES="../../data/reference/guacamol_v1_train.csv"
NUM_GENERATED=10000
# NUM_REFERENCE=100000
# OUTPUT_FILE="./GuacaMolEval.json"  # same as default


if [ ! -f "$EVAL_SCRIPT" ]; then
  echo "Could not find $EVAL_SCRIPT, exit."
  exit
fi

if [ ! -f "$GENERATED_MOLECULES" ]; then
  echo "Could not find $GENERATED_MOLECULES, exit."
  exit
fi

if [ ! -f "$REFERENCE_MOLECULES" ]; then
  echo "Could not find $REFERENCE_MOLECULES, exit."
  exit
fi


echo "Evaluation molecules..."
echo

echo "Starting evaluation at $(date +%T)..."

python eval.py \
  -g "$GENERATED_MOLECULES" \
  -m "$NUM_GENERATED" \
  -r "$REFERENCE_MOLECULES" \
  -n 2000 \
  -o "../../data/generated/GuacaMolEval_num_2000_pad_350.json"
python eval.py \
  -g "$GENERATED_MOLECULES" \
  -m "$NUM_GENERATED" \
  -r "$REFERENCE_MOLECULES" \
  -n 10000 \
  -o "../../data/generated/GuacaMolEval_num_10000_pad_350.json"
python eval.py \
  -g "$GENERATED_MOLECULES" \
  -m "$NUM_GENERATED" \
  -r "$REFERENCE_MOLECULES" \
  -n 50000 \
  -o "../../data/generated/GuacaMolEval_num_50000_pad_350.json"
python eval.py \
  -g "$GENERATED_MOLECULES" \
  -m "$NUM_GENERATED" \
  -r "$REFERENCE_MOLECULES" \
  -n 250000 \
  -o "../../data/generated/GuacaMolEval_num_250000_pad_350.json"

date +"---- Finished evaluation at %T"
