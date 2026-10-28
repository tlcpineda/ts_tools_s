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
    filter_files,
    get_term_details,
    hor_bar,
    identify_path,
    load_csv,
    load_proj_cache,
    parse_pathname,
    rename_path,
    select_cached_proj_for_update,
    show_proj_in_cache,
    show_proj_param,
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


def update_dims() -> None:
    cache = load_proj_cache(PROJ_CACHE)

    proj_ind, proj_det = select_cached_proj_for_update(cache)

    show_proj_param(cache, proj_det, "dim")

    print("\n>>> Append new values ?")
    update_resp = input("\n>>>  [Y]es/[N]o : ").strip()

    # Terminate process; case where values are already in cache log.
    if update_resp.upper() not in ["Y", ""]:
        return

    print("\n>>> Enter new dimension, and resolution values, for the term : ")
    update_values = {"term": 0, "w": 0, "h": 0, "r": 0}

    for key in update_values:
        update_values[key] = int(input(f">>>  New {key} : "))

    update_cached_proj_field(cache, proj_ind, "dim", update_values)


def prepare_files() -> None:
    try:
        cache = load_proj_cache(PROJ_CACHE)
        sole_id, proj_name, term, chapters = get_term_details(cache)
        num_chapters = len(chapters)
        term_ref_folder = parse_pathname(PARENT_LOCAL, proj_name, f"{term} JPEG", "folder")

        for ind, ch in enumerate(chapters):
            term_jpg_ref_folder_name = f"{int(sole_id):010}_{lang_iso_2_ref}_{ch}"
            term_psd_ref_folder = parse_pathname(term_ref_folder, term_jpg_ref_folder_name, "PSD", "folder")

            # Case when PSD folder within reference JPEG folder is absent; possibly JPEG files not yet initialised.
            if not os.path.exists(term_psd_ref_folder):
                display_message("WARN", f"Folder .../{term_jpg_ref_folder_name}/PSD does not exists.")
                continue

            psd_files = filter_files(term_psd_ref_folder)
            psd_files.sort(key=is_copyright)

            hor_bar(100, f"Processing folder {ind + 1} / {num_chapters} ... ")
            display_path_desc(term_psd_ref_folder, "folder")

            chapter_name = f"{int(sole_id):010}_{lang_iso_2}_{ch}"
            term_chapter_work_folder_name = f"{proj_name}/T{term} - {chapter_name}"
            term_psd_work_folder_name = f"{chapter_name}"

            term_psd_work_folder = parse_pathname(
                PARENT_LOCAL, term_chapter_work_folder_name, term_psd_work_folder_name, "folder"
            )

            dest_exists = ensure_path_exists(term_psd_work_folder, "folder")

            # Fringe case when destination folder is not present, nor successful created from previous line.
            if not dest_exists:
                display_message("WARN", f"Target folder ( .../{term_psd_work_folder_name} ) not found.")
                continue

            for ind, file in enumerate(psd_files):
                base, ext = os.path.splitext(file)
                ext = ext[1:]

                # Copy reference PSD file to working folder.
                copy_file(
                    term_psd_ref_folder,
                    term_psd_work_folder,
                    base,
                    ext
                )

                # Rename files in working folder; append 4-char ordinal numbering after space.
                rename_path(
                    parse_pathname(term_psd_work_folder, base, ext, "file"),
                    parse_pathname(term_psd_work_folder, f"{base} {ind:04}", ext, "file"),
                    "file"
                )

            print()

    except Exception as e:  # noqa: BLE001
        display_message(
            "ERROR", "Failed to sort reference files to working directories.", f"{e}"
        )


def is_copyright(dest_path: str) -> int:
    """
    Identify if filename has "copyright" in its name. Push file to last of sorting order.
    """
    filename = os.path.basename(dest_path)

    try:
        # Check if "copyright" is in filename.
        return 1 if "copyright" in filename.lower() else 0

    except Exception as e:  # noqa: BLE001
        display_message("ERROR", "Failed to get sorting key from PSD filename.", f"{e}")
        return 0    # Fallback value.


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
                "\n>>>  [P]repare working files ?"
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
                prepare_files()
            elif resp == "A":
                analyse_ref_files()
            elif resp == "U":
                update_dims()
