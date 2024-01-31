# coding=utf-8
import argparse
from pathlib import Path
from typing import Final, Union

import pandas as pd
from guacamol.assess_distribution_learning import assess_distribution_learning
from guacamol.distribution_matching_generator import DistributionMatchingGenerator
from loguru import logger

from guacamoleval.helpers import configure_logging, guess_project_root_dir

DEFAULT_OUTPUT_FILE_NAME: Final[str] = "GuacaMolEval.json"
DEFAULT_NUM_GEN_MOLECULES: Final[int] = 10_000
VALID_ONLY: Final[bool] = True
REFERENCE_MOLECULES_PATH: Final[Path] = (
    guess_project_root_dir() / "./data/reference/guacamol_v1_train.csv"
)


class GuacaMolEval(DistributionMatchingGenerator):
    def __init__(self, file_path: Union[str, Path], valid_only: bool = False) -> None:
        # super.__init__()
        self.file_path = Path(file_path).resolve()
        self.valid_only = valid_only
        self._molecules: list[str] = self._read_molecules_from_file(
            self.file_path, self.valid_only
        )

    @staticmethod
    def _read_molecules_from_file(
        file_path: Path, valid_only: bool = False
    ) -> list[str]:
        """Read molecules from a CSV file.
        Args:
            file_path: the path to the CSV file.
            valid_only: whether to only return valid molecules. Defaults to False.

        Returns:
            A list of molecules as strings.

        Raises:
            ValueError: if num_molecules is greater than the number of molecules in the file.
        """

        # Cope with different column names, allows for several columns names or no header
        # Note: we read the "smiles" column and ignore the "canonical_smiles" column
        # That does not matter since we canonicalize the molecules anyway during evaluation

        molecules_df: pd.Series | pd.DataFrame
        try:
            molecules_df = pd.read_csv(file_path, usecols=["smiles", "valid"])
            if valid_only:
                molecules_df = molecules_df[molecules_df["valid"]]["smiles"]
            else:
                molecules_df = molecules_df["smiles"]

        except ValueError as e:
            try:
                molecules_df = pd.read_csv(file_path, usecols=["smiles"])
            except ValueError:
                molecules_df = pd.read_csv(file_path, header=None, usecols=[0])
            if valid_only:
                raise ValueError(
                    "The 'valid_only' option is not supported for this file, check file format"
                ) from e

        # Delete rows with NaN values
        molecules: list[str] = molecules_df.dropna().values.astype(str).tolist()
        return molecules

    def generate(self, number_samples: int) -> list[str]:
        if number_samples > len(self._molecules):
            adjective_str = "valid" if self.valid_only else "generated"
            raise ValueError(
                f"The number of molecules to be evaluated ({number_samples:,d}) is greater than "
                f"the number of {adjective_str} molecules ({len(self._molecules):,d})"
            )
        return self._molecules[:number_samples]


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate generated molecules with GuacaMol Distribution Learning Benchmark."
    )
    parser.add_argument(
        "-g",
        "--generated",
        type=Path,
        required=True,
        help="file path to the generated molecules.",
    )
    parser.add_argument(
        "-m",
        "--num_gen_mols",
        type=int,
        required=False,
        default=DEFAULT_NUM_GEN_MOLECULES,
        help="number of molecules to evaluate from generated molecules, default: '%(default)s'",
    )
    parser.add_argument(
        "-n",
        "--num_ref_mols",
        type=int,
        required=False,
        help="number of molecules to evaluate from reference molecules, default: all reference molecules.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=False,
        default=None,
        help=f"file path for the evaluation statistic, "
        f"default: {DEFAULT_OUTPUT_FILE_NAME} in the directory of the generated molecules.",
    )
    parser.add_argument(
        "-r",
        "--reference",
        type=Path,
        required=False,
        default=REFERENCE_MOLECULES_PATH,
        help="file path to the reference (GuacaMol training set) molecules, default: '%(default)s'.",
    )

    return parser.parse_args()


@logger.catch
def main() -> None:
    configure_logging()

    args = get_args()

    args.generated = args.generated.resolve()
    if not args.generated.is_file():
        raise ValueError(f"File '{args.generated}' does not exist.")
    if args.num_gen_mols < 3:
        raise ValueError("Number of generated molecules must be at least 3.")
    logger.info(
        f"Reading {args.num_gen_mols} generated molecules from {args.generated}"
    )

    if args.num_ref_mols < 3:
        raise ValueError("Number of reference molecules must be at least 3.")
    args.reference = args.reference.resolve()
    if not args.reference.is_file():
        raise ValueError(f"File '{args.reference}' does not exist.")
    logger.info(
        f"Reading {args.num_ref_mols} refenence molecules from {args.reference}"
    )

    if args.output is None:
        args.output = args.generated.parent / DEFAULT_OUTPUT_FILE_NAME
    else:
        args.output = args.output.resolve()
        args.output.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing evaluation statistic to {args.output}")

    evaluator = GuacaMolEval(args.generated)
    assess_distribution_learning(
        model=evaluator,
        chembl_training_file=args.reference,
        number_generated_samples=args.num_gen_mols,
        number_reference_samples=args.num_ref_mols,
        json_output_file=args.output,
    )


if __name__ == "__main__":
    main()
