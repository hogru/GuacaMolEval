# coding=utf-8
import argparse

from guacamol.distribution_matching_generator import DistributionMatchingGenerator
from guacamol.assess_distribution_learning import assess_distribution_learning
from typing import Final, Union
from pathlib import Path
import pandas as pd  # type: ignore
import argparse

DEFAULT_OUTPUT_FILE_NAME: Final[str] = "GuacaMolEval.json"
DEFAULT_NUM_MOLECULES: Final[int] = 10000
VALID_ONLY: Final[bool] = True
TEMP_MOLECULES_PATH: Final[str] = "/home/stephan/code/guacamoleval/data/samples/generated_smiles.csv"
TEMP_GUACAMOL_PATH: Final[str] = "/home/stephan/code/guacamoleval/data/guacamol/guacamol_v1_train.csv"


class GuacaMolEval(DistributionMatchingGenerator):
    def __init__(self, file_path: Union[str, Path], valid_only: bool = False) -> None:
        # super.__init__()
        self.file_path = Path(file_path).resolve()
        self.valid_only = valid_only
        self._molecules: list[str] = self._read_molecules_from_file(self.file_path, self.valid_only)

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
        molecules_df: pd.DataFrame
        try:
            molecules_df = pd.read_csv(file_path, usecols=["smiles", "valid"])
            # TODO make this a configurable option: if we want novel molecules only
            # molecules_df = pd.read_csv(file, usecols=["smiles", "valid", "novel"])
            if valid_only:
                molecules_df = molecules_df[molecules_df["valid"]]["smiles"]
                # The 2nd required code line for the option mentioned above
                # molecules_df = molecules_df[molecules_df["valid"] & molecules_df["novel"]]["smiles"]
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
        molecules: list[str] = molecules_df.dropna().values.squeeze()
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
        "-n",
        "--num_molecules",
        type=int,
        required=False,
        default=DEFAULT_NUM_MOLECULES,
        help="number of molecules to evaluate from generated molecules, default: '%(default)s'",
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
        required=True,
        help="file path to the GuacaMol training molecules.",
    )

    return parser.parse_args()


def main() -> None:
    # args = get_args()
    evaluator = GuacaMolEval(TEMP_MOLECULES_PATH, VALID_ONLY)
    assess_distribution_learning(model=evaluator,
                                 chembl_training_file=TEMP_GUACAMOL_PATH,
                                 json_output_file=DEFAULT_OUTPUT_FILE_NAME)


if __name__ == '__main__':
    main()
