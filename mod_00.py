import os

from dotenv import load_dotenv
from PIL import Image

from lib import (
    clean_number,
    copy_file,
    display_message,
    display_path_desc,
    ensure_path_exists,
    expand_path,
    get_term_details,
    hor_bar,
    identify_path,
    load_csv,
    load_proj_cache,
    parse_pathname,
    rename_path,
    show_proj_in_cache,
    show_table,
    update_cached_proj_field,
    welcome_sequence,
    write_to_csv,
)

# Module variables
mod_name = "Preliminary Administrative Works"
mod_ver = "1"
date = "26 Oct 2026"
email = "tlcpineda.projects@gmail.com"

# Two-character language ISO code
lang_iso_2_ref = "jp"
lang_iso_2 = "en"

# Load .env file.
load_dotenv()
BOX_DEV_CONSOLE = os.getenv("BOX_DEV_CONSOLE", "")
PROJ_CACHE = expand_path(os.getenv("PROJ_CACHE", ""))
PARENT_LOCAL = expand_path(os.getenv("PARENT_LOCAL", ""))


def analyse_ref_files() -> None:
    term_ch_summary = {}

    try:
        cache = load_proj_cache(PROJ_CACHE)
        sole_id, proj_name, term, chapters = get_term_details(cache)

        for ch in chapters:
            term_ch = f"{term} JPEG/{int(sole_id):010}_{lang_iso_2_ref}_{ch}"
            ch_ref_path = parse_pathname(PARENT_LOCAL, proj_name, term_ch, "folder")

            # Ensure that reference folder exists;
            # may be empty, in case of newly-created folders
            path_exists = ensure_path_exists(ch_ref_path)

            if not path_exists:
                continue

            print()
            hor_bar(100, f"Analysing files in .../{term_ch} ...")

            # Initialize frequency counters for the current folder.
            metrics = {
                "height": {},
                "width": {},
                "dpi": {},
                "count": 0
            }

            files_in_path = os.listdir(ch_ref_path)

            # In case folder is empty
            if not files_in_path:
                continue

            # Iterate through items in the directory.
            for filename in files_in_path:
                # Filter for JPEG extensions case-insensitively.
                if filename.lower().endswith((".jpg", ".jpeg")):
                    file_path = os.path.join(ch_ref_path, filename)

                    try:
                        # Open image metadata without loading full pixel data.
                        with Image.open(file_path) as img:
                            width, height = img.size

                            # Extract DPI tuple from image info, handling potential missing values.
                            dpi = img.info.get("dpi", (0, 0))
                            if isinstance(dpi, tuple) and len(dpi) > 0:
                                resolution = int(dpi[0]) if dpi[0] else 0
                            else:
                                resolution = 0

                            # Update metrics counters.
                            metrics["width"][width] = metrics["width"].get(width, 0) + 1
                            metrics["height"][height] = metrics["height"].get(height, 0) + 1
                            metrics["dpi"][resolution] = metrics["dpi"].get(resolution, 0) + 1
                            metrics["count"] = metrics.get("count", 0) + 1

                    except Exception as img_err:  # noqa: BLE001
                        display_message("WARN", f"Could not read image metadata for {filename}.", f"{img_err}")
            # Temporary check to verify data capture per folder.
            print(f"Analysed {metrics["count"]} file{"s" if metrics["count"] > 1 else ""} in CH{ch}.")

            ch_metrics = {}

            for param in ["count", "width", "height", "dpi"]:
                ch_metrics[param] = metrics[param] if param == "count" else get_mode(metrics[param])
                term_ch_summary[ch] = ch_metrics

            hor_bar(100)

        summary_table = [
            [
                ch,
                v["count"],
                ", ".join([f"{w} ({cw})" for w, cw in v["width"]]),
                ", ".join([f"{h} ({cht})" for h, cht in v["height"]]),
                ", ".join([f"{dpi} ({cdpi})" for dpi, cdpi in v["dpi"]])
            ]
            for ch, v in term_ch_summary.items()
        ]

        show_table(
            "TERM-CHAPTER FILE ANALYSIS SUMMARY",
            [12, 12, 12, 12, 12],
            ["Chapter", "File Count", "Width (px)", "Height (px)", "Res. (dpi)"],
            summary_table
        )

    except Exception as e:  # noqa: BLE001
        display_message("ERROR", "Failed to analyse reference files.", f"{e}")


def get_mode(counts: dict) -> list[tuple[int, int]]:
    if not counts:
        return []

    max_freq = max(counts.values())
    return [(val, freq) for val, freq in counts.items() if freq == max_freq]


def update_dims() :
    cache = load_proj_cache(PROJ_CACHE)

    display_message("INFO", "Enter new dimension, and resolution values, for the term.")
    update_values = {"term": 0, "w": 0, "h": 0, "r": 0}

    for key in update_values:
        update_values[key] = int(input(f"Enter {key} : "))

    update_cached_proj_field(cache, "dim", update_values)


# def prepare_files() -> None:
#     ref_jpg_ch_folders = []
#     ref_psd_ch_folders = []
#     w_psd_ch_folders = []
#
#     try:
#         cache = load_proj_cache(PROJ_CACHE)
#         sole_id, proj_name, term, chapters = get_term_details(cache)
#
#         term_ref_folder = parse_pathname(PARENT_LOCAL, proj_name, f"{term} JPEG", "folder")


#         # Summarising contents of recently created folders.
#         summary_table = []
#
#         for index, folder in enumerate(
#             ref_psd_ch_folders + ref_jpg_ch_folders + w_psd_ch_folders
#         ):
#             summary_table.append(
#                 [
#                     index + 1,
#                     f".../{'/'.join((folder.split('/' if '/' in folder else os.sep))[-2:])}",
#                     f"{len(os.listdir(folder)):6}",
#                     "※"
#                     if index > len(ref_psd_ch_folders + ref_jpg_ch_folders) - 1
#                     else "",
#                 ]
#             )
#
#         show_table(
#             f"New Folders in .../2 PROJECTS/{proj_name}",
#             [4, 50, 10, 1],
#             ["Item", "Directory", "Contents", ""],
#             summary_table,
#         )
#
#         print("※ Files require adjustments in resolution and dimensions.")

#     except Exception as e:
#         display_message(
#             "ERROR", "Failed to sort reference files to working directories.", f"{e}"
#         )


def verify_contents_ref_folder(
    fnames: list[str], files_desc: str
) -> tuple[str, int | str]:
    print(f"\n>>> {files_desc} : ")

    ref_folder = str(identify_path("folder"))

    if not ref_folder:
        print("\n>>> No folder selected.")
        return "", "NA"

    _, base = display_path_desc(ref_folder, "folder")
    display_message("INFO", f"Verifying contents of folder '{base}' ...")

    ref_contents = os.listdir(ref_folder)
    missing_files = [name for name in fnames if name not in ref_contents]
    num_missing_files = 0

    if missing_files:
        num_missing_files = len(missing_files)
        display_message("WARN", f"Missing files ({num_missing_files}) from '{base}' :")
        print(f"<=>  {'\n<=>  '.join(missing_files)}\n")
    else:
        display_message("INFO", f"All required files in '{base}'.")

    return ref_folder, num_missing_files


# def gen_pagination() -> tuple[list[list[str]], str, str, str]:
#     """
#     :return: csv_data, proj_name, vol_num, title_vol
#     """
#     try:
#         cache = load_proj_cache(PROJ_CACHE)
#         work_id, proj_name, title_en, vol_num, _, _ = get_term_details(cache)
#         title_vol = f"{title_en}_{int(vol_num):03}"
#
#         print(f"\n<=> Generating pagination data for ' {title_vol} ' ... ")
#
#         csv_data = []
#
#         # Check if CSV file exists from previous run.
#         csv_path = os.path.join(
#             PARENT_LOCAL, proj_name, f"{csv_name_pre} {title_vol}.csv"
#         )
#
#         if os.path.exists(csv_path):
#             display_message("INFO", "Pagination data loaded from CSV file ... ")
#             csv_data, _ = load_csv(csv_path)
#
#         else:
#             # Tkinter method to process pagination data, pasted from webapp.
#             csv_data = get_webapp_data(work_id, vol_num, title_vol)
#             write_to_csv(csv_path, csv_heads + csv_data)
#
#         return csv_data, proj_name, vol_num, title_vol
#
#     except Exception as e:
#         display_message("ERROR", "Failed to generate pagination data.", f"{e}")
#
#         return [], "", "", ""

# def str_to_list(raw_text: str) -> list[list[str,]]:
#     items = [item.strip() for item in raw_text.split("\n") if item.strip()]
#
#     if not items:
#         display_message("WARN", "No data found.")
#         return []
#
#     total_count = len(items)
#
#     display_message("INFO", f"Total of {total_count} number of data retrieved.")
#
#     # Perform the Multiple Check.
#     remainder = total_count % cols
#
#     if remainder != 0:
#         n1 = total_count - remainder
#
#         display_message(
#             "ERROR",
#             f"Expected {n1}, or {n1 + cols}; or multiples of {cols} number of data.",
#         )
#
#         return []
#
#     display_message("SUCCESS", "Pagination data parsed.  Ready to write to CSV.")
#
#     return [items[i : i + cols] for i in range(0, total_count, cols)]

if __name__ == "__main__":
    welcome_sequence([mod_name, f"ver {mod_ver} {date}", email])

    print(input("\n>>> Press enter to continue ..."))

    confirm_exit = False

    while not confirm_exit:
        proper_resp = False
        resp = "C"

        while not proper_resp:
            print(
                "\n>>> Select an option :"
                "\n>>>  [A]nalyse reference files ?"
                "\n>>>  [P]repare reference files ?"
                "\n>>>  [U]pdate project cache dimensions ?"
                "\n>>>  E[X]it and close this window ?"
            )

            resp = input(">>> ").upper()

            proper_resp = resp in ["A", "P", "U", "X"]

        if resp == "X":
            print("\n<=> Closing down ...")

            confirm_exit = True
        else:
            confirm_exit = False

            if resp == "P":
                # prepare_files()
                pass
            elif resp == "A":
                analyse_ref_files()
            elif resp == "U":
                update_dims()
