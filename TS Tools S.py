"""
A compilation of modules to assist in local processes during typesetting,
and some Box API operations, for Project S.
"""

from lib import display_message, hor_bar, welcome_sequence
from mod_00 import analyse_ref_files, prepare_files, update_dims
from mod_01A import create_pre_csv
from mod_01B import finalise_csv
from mod_03 import compile_revision
from mod_04 import create_term_tree, fetch_cr, fetch_data_files, fetch_tl

# App variables
app_name = "Typesetting Tools S"
app_ver = "2.00.00"
date = "20 Nov 2026"
email = "tlcpineda.projects@gmail.com"
options = [
    {
        "menu": "(LOC) [A]nalyse reference files",
        "shortkey": "A",
        "func": analyse_ref_files,
    },
    {
        "menu": "(LOC) [P]repare reference files",
        "shortkey": "P",
        "func": prepare_files,
    },
    {
        "menu": "(LOC) [U]pdate cache dimensions",
        "shortkey": "U",
        "func": update_dims,
    },
    {
        "menu": "(LOC) [S]crape translations",
        "shortkey": "S",
        "func": create_pre_csv,
    },
    {
        "menu": "(LOC) [F]inalise translations CSV",
        "shortkey": "F",
        "func": finalise_csv,
    },

    {
        "menu": "(LOC) Compile [R]evision files",
        "shortkey": "R",
        "func": compile_revision,
    },

    {
        "menu": "(BOX) [C]reate typesetting term folder",
        "shortkey": "C",
        "func": create_term_tree,
    },
    {
        "menu": "(BOX) Fetc[H] translation file/s",
        "shortkey": "H",
        "func": fetch_tl,
    },
    {
        "menu": "(BOX) [D]ownload source files",
        "shortkey": "D",
        "func": fetch_data_files,
    },
    {
        "menu": "(BOX) F[E]etch Client revision file",
        "shortkey": "E",
        "func": fetch_cr,
    },
    {"menu": "E[X]it and close window", "shortkey": "X"},
]


def display_menu():
    print()

    hor_bar(60, "MENU")

    for option in options:
        print(f"{' ':5}{option['menu']}")

    hor_bar(60)

    print("\n>>> Select an option ...")


if __name__ == "__main__":
    welcome_sequence(
        [
            app_name,
            f"ver {app_ver} {date}",
            email,
        ]
    )

    confirm_exit = False

    while not confirm_exit:
        display_menu()
        user_input = None

        while not user_input:
            resp = input(">>> ").upper().strip()

            if resp in [option["shortkey"] for option in options]:
                user_input = resp
            else:
                display_message("WARN", "Invalid option.")

        if user_input == "X":
            hor_bar(60, "CLOSING DOWN ...")
            confirm_exit = True
        else:
            print()

            selected_option = next(
                option for option in options if option["shortkey"] == user_input
            )
            func_selected = selected_option["func"]  # requires input_path

            hor_bar(60, f"RUNNING : {func_selected.__name__}()")
            func_selected()
            hor_bar(60, f"COMPLETE : {func_selected.__name__}()")
