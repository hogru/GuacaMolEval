#!/bin/bash
# Sample script to evaluate molecules with Guacamol
# Current directory should contain the python scripts
# i.e. src/guacamoleval/

EVAL_SCRIPT="eval.py"
GENERATED_MOLECULES="../../data/generated/generated_smiles.csv"
REFERENCE_MOLECULES="../../data/reference/guacamol_v1_train.csv"
NUM_GENERATED=10000
NUM_REFERENCE=100000
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
echo "  Taking $NUM_GENERATED molecules from: $GENERATED_MOLECULES"
echo "  Taking $NUM_REFERENCE molecules from: $REFERENCE_MOLECULES"
echo

echo "Starting evaluation at $(date +%T)..."
python eval.py \
  -g "$GENERATED_MOLECULES" \
  -m "$NUM_GENERATED" \
  -r "$REFERENCE_MOLECULES" \
  -n "NUM_REFERENCE"
date +"---- Finished evaluation at %T"
