import os
import time

from dotenv import load_dotenv

from box_lib import (
    copy_box_entry,
    display_box_path,
    dl_box_entry,
    ensure_box_folder_exists,
    extract_entry_meta,
    fetch_entry,
    find_box_entry_by_name,
    get_box_entries,
    init_client,
    move_box_entry,
    parse_box_url,
    rename_box_entry,
)
from lib import (
    LogManager,
    display_message,
    display_path_desc,
    ensure_path_exists,
    expand_path,
    get_cached_proj_details,
    get_term_details,
    hor_bar,
    load_csv,
    load_proj_cache,
    parse_pathname,
    show_table,
    welcome_sequence,
)

# import win32com.client as win32
# from datetime import datetime
# from mod_00 import parse_ch_name

# Module variables
mod_name = "Box API Operations"
mod_ver = "1"
date = "26 Oct 2026"
email = "tlcpineda.projects@gmail.com"
lang_iso_2 = "en"

# Load .env file.
load_dotenv()
PROJ_CACHE = expand_path(os.getenv("PROJ_CACHE", ""))
BOX_PARENT = os.getenv("BOX_PARENT", "")
PARENT_LOCAL = expand_path(os.getenv("PARENT_LOCAL", ""))


def box_delay(sec: int) -> None:
    time.sleep(sec)

def fetch_data_files() -> None:
    try:
        sources = []    # Box URLs of typesetting folders, by chapter, containing source JPEG files.
        cache = load_proj_cache(PROJ_CACHE)
        sole_id, proj_name, term, chapters = get_term_details(cache)

        client = init_client()

        if not client:
            raise RuntimeError("Failed to create Box client.")

        parent = BOX_PARENT  #Initialise parent to project parent Box folder.

        # Find folders (IDs) containing files to be downloaded (by chapter) from "01" folder.
        # parent >> term >> 01 >> proj_id >> chapters
        for folder_name in [term, "01", sole_id, [f"_{ch}" for ch in chapters]]:
            if isinstance(folder_name, str):
                target = find_box_entry_by_name(
                    client, parent, "folder", folder_name, True
                )

                if target:  # target becomes parent.
                    parent = parse_box_url("folder", target.id)

            elif isinstance(folder_name, list):
                for sibling in folder_name:
                    target = find_box_entry_by_name(
                        client, parent, "folder", sibling, True
                    )

                    if target:
                        source_id = target.id
                        sources.append((source_id, "folder"))

        # Download data Box folders to local drive
        zip_dest_path = parse_pathname(
            os.path.join(PARENT_LOCAL, proj_name),
            f"{term} JPEG",
            "zip",
            "file",
        )

        dl_box_entry(client, sources, zip_dest_path)

    except Exception as e:  # noqa: BLE001
        display_message("ERROR", "Failed to fetch typesetting data from Box.", f"{e}")


def fetch_tl() -> None:
    try:
        tl_docs = []    # Box URLs of translation files; usually by chapter.
        cache = load_proj_cache(PROJ_CACHE)
        sole_id, proj_name, term, chapters = get_term_details(cache)

        client = init_client()

        if not client:
            raise RuntimeError("Failed to create Box client.")

        parent = BOX_PARENT  #Initialise parent to project parent Box folder.

        # Find translation files (IDs) to be downloaded (individually) from "02" folder.
        # parent >> term >> 02 >> proj_id
        for folder_name in [term, "02", sole_id]:
            source = find_box_entry_by_name(
                client, parent, "folder", folder_name, True
            )

            if source:  # source becomes parent.
                parent = parse_box_url("folder", source.id)
            else:
                raise RuntimeError("Failed to trace parentage.")

        tl_docs = get_box_entries(client, parent)

        if not tl_docs:
            raise RuntimeError(f"Failed to list translation documents for Term{term}.")

        dl_info = {}

        for ch in chapters:
            display_message("INFO", f"File Selection for CH{ch} ... ")

            show_table(
                f"Term{term}-{sole_id} Translations",
                [3, 13, 20],
                ["DOC", "Box ID", "Filename"],
                [[i + 1, doc.id, doc.name] for i, doc in enumerate(tl_docs) if doc],
            )

            # Select file to download by "DOC" number.
            resp = False
            doc_num = 0
            tl_id = ""
            tl_bname = ""
            tl_extname = ""

            while not resp:
                doc_num = int(
                    input(
                        f'\n>>> Enter "DOC" number for CH{ch} ("0" to skip chapter): '
                    ).strip()
                )

                if doc_num in range(1, len(tl_docs) + 1):
                    resp = True
                elif doc_num == 0:
                    display_message("WARN", f"Skip {ch}.")
                    resp = True
                else:
                    display_message("WARN", f'"{doc_num}" is not a valid input.')

            if doc_num:
                # Pick entry ID based on DOC number; index of tl_docs.
                tl_file = tl_docs[int(doc_num) - 1]

                if tl_file:
                    tl_id = tl_file.id
                    tl_bname, tl_extname = os.path.splitext(tl_file.name or "")
                    entry_url = parse_box_url("file", tl_id)

                    display_message("INFO", "Translation file selected for download.")
                    display_box_path(client, entry_url)

                    tl_dest_p = os.path.join(PARENT_LOCAL, proj_name, f"T{term} - {int(sole_id):010}_{lang_iso_2}_{ch}")
                    tl_dest = parse_pathname(tl_dest_p, tl_bname, tl_extname[1:], "file")

                    dl_info[ch] = {"box_id": tl_id, "dest_path": tl_dest}

        for k, v in dl_info.items():
            f_id = v["box_id"]
            f_dest = v["dest_path"]

            ensure_path_exists(f_dest, "file")

            display_message("INFO", f"Downloading translation file for CH{k} (ID : {f_id}) ... ")
            display_path_desc(f_dest, "file")

            dl_stat = dl_box_entry(client, f_id, f_dest)

            if dl_stat:
                display_message("SUCCESS", "File successfully download.")
            else:
                raise RuntimeError("Failed to download file.")

    except Exception as e:  # noqa: BLE001
        display_message("ERROR", "Failed to fetch translation document.", f"{e}")
        return

# def move_pdf():
#     client = init_client()
#
#     if not client:
#         return
#
#     while True:
#         parent_url = input(
#             "\n>>> Input URL of folder to be processed ('Q' to quit) : "
#         ).strip()
#
#         if not parent_url:
#             display_message("WARN", "No URL input.")
#             continue
#
#         if parent_url.upper() == "Q":
#             display_message("WARN", "Terminating process.")
#             break
#
#         parent_type, parent_id = extract_entry_meta(parent_url)
#
#         if not parent_id or parent_type != "folder":
#             display_message("ERROR", "Invalid Box folder URL.")
#             continue
#
#         try:
#             parent = fetch_entry(client, parent_url, ("info", {}))
#
#             if not parent:
#                 display_message("ERROR", "Invalid Box folder URL.")
#
#             hor_bar(100)
#             display_message("INFO", f"Processing folder (ID : {parent_id})")
#
#             folder_entries = get_box_entries(client, parent_url)
#             len_f_entries = len(folder_entries)
#
#             for folder_i, folder in enumerate(folder_entries):
#                 # folder_id = folder.id
#                 folder_url = parse_box_url("folder", folder.id)
#                 folder_name = folder.name
#
#                 display_message(
#                     "INFO",
#                     f"Processing folder ( {folder_i + 1} / {len_f_entries} ) ... ",
#                 )
#                 display_box_path(client, folder_url)
#                 display_message("INFO", "Retrieving Box entries ... ")
#
#                 subentries = get_box_entries(client, folder_url)
#                 target_name = f"{folder_name}.pdf"
#                 target_entry = [
#                     entry
#                     for entry in subentries
#                     if (entry.type == "file" and entry.name == target_name)
#                 ]
#
#                 if len(target_entry) != 1:
#                     display_message(
#                         "ERROR",
#                         f"Something wrong with target PDF file, {target_name}.\
#                         \nVerify contents of parent folder ( {folder_url} )",
#                     )
#                     break
#
#                 target_url = parse_box_url("file", target_entry[0].id)
#
#                 move_box_entry(client, target_url, True)
#                 # print(f'Moving "{target_url}" ... ')
#
#                 hor_bar(100)
#                 box_delay(1)
#             break
#
#         except Exception as e:
#             display_message("ERROR", "Failed to move PDF files to term folder.", f"{e}")
#             break
#
# def create_term_tree() -> dict[str, str]:
#     chapter_urls = {}
#     # TODO Implement active search; Project S_TLTS > Term_num > FOLDER_TYPE > Project_code > ch_num
#     parent_url = ""
#     client = init_client()
#
#     if not client:
#         display_message("ERROR", "Failed to create BoxClient object.")
#         return {}
#
#     cache = load_proj_cache(PROJ_CACHE)
#     _, proj_name, term, _ = get_term_details(cache)
#     box_delay(2)
#
#     try:
#         for branch_name in [term, proj_name, ch]:
#             if isinstance(branch_name, str):
#                 hor_bar(100)
#                 box_delay(2)
#
#                 branch_id = ensure_box_folder_exists(client, parent_url, branch_name)
#
#                 if branch_id:
#                     parent_url = parse_box_url("folder", branch_id)
#
#             elif isinstance(branch_name, list):
#                 for sibling in branch_name:
#                     hor_bar(100)
#                     box_delay(2)
#                     sibling_id = ensure_box_folder_exists(client, parent_url, sibling)
#                     chapter_urls[sibling] = parse_box_url("folder", sibling_id)
#
#         hor_bar(100)
#
#         show_table(
#             f"New Box Folders for {term} : {proj_name.split(' ')[0]} {title_en}",
#             [3, 10, 50],
#             ["", "Chapters", "Folder URL"],
#             [[i + 1, k, v] for i, (k, v) in enumerate(chapter_urls.items())],
#         )
#
#         return chapter_urls
#
#     except Exception as e:  # noqa: BLE001
#         display_message("ERROR", "Failed to create term tree in Box.", f"{e}")
#         return {}


# def copy_ts_files():
#     """
#     Copy latest revision typesetting files (PDF/JPEG)
#     where chapter has no client feedback/request for revisions.
#     """
#     client = init_client()
#
#     # Terminate process when BoxClient is not created.
#     if not client:
#         return
#
#     cache = load_proj_cache(PROJ_CACHE)
#     source_parent = TS_PARENT
#     dest_parent = CR_PARENT
#     sources = {}
#
#     _, proj_name, _, _, term, ch = get_term_details(cache)
#
#     if not client:
#         display_message("ERROR", "Failed to create BoxClient object.")
#         return
#
#     try:
#         # Find folders (IDs) containing files to be copied (by chapter) from Typesetting folder;
#         # and, the folder (ID) where the files are to be sent revisions folder.
#         for folder_name in [term, proj_name, ch]:
#             if isinstance(folder_name, str):
#                 source = find_box_entry_by_name(
#                     client, source_parent, "folder", folder_name
#                 )
#
#                 if source:  # source becomes source_parent.
#                     source_parent = parse_box_url("folder", source.id)
#
#                 # Assign new destination parent; create new, when required.
#                 dest_id = ensure_box_folder_exists(client, dest_parent, folder_name)
#                 dest_parent = parse_box_url("folder", dest_id)
#
#             elif isinstance(folder_name, list):
#                 for sibling in folder_name:
#                     source = find_box_entry_by_name(
#                         client, source_parent, "folder", sibling
#                     )
#
#                     if source:
#                         source_id = source.id
#                         sources[sibling] = parse_box_url("folder", source_id)
#
#         # Copy source folders to destination.
#         for ch, url in sources.items():
#             hor_bar(100)
#             box_delay(1)  # 2-sec delay between sources
#             copy_box_entry(client, url, dest_parent)
#
#     except Exception as e:
#         display_message("ERROR", f"Failed to copy typesetting files.{e}")


# def fetch_client_cr() -> None:
#     def get_range_from_name(entry_name) -> range:
#         id_range = range(0)
#
#         base, _ = os.path.splitext(entry_name)
#         str_range = base.split("No.")[1]
#
#         i, o = str_range.split("-")
#
#         id_range = range(int(i), int(o) + 1)
#
#         return id_range
#
#     def purge_xlsx(xlsx_path: str, tab_name: str, work_id: str):
#         """
#         Open a local Excel file natively through Windows COM.
#         Keep first two tabs and the project tab,
#         and delete all other tabs.
#         """
#         excel_app = win32.Dispatch("Excel.Application")
#         excel_app.Visible = False
#         excel_app.DisplayAlerts = False
#
#         display_message("INFO", "Purging Client CR file ... ")
#         _, base = display_path_desc(xlsx_path, "file")
#
#         try:
#             workbook = excel_app.Workbooks.Open(
#                 Filename=xlsx_path, CorruptLoad=win32.constants.xlRepairFile
#             )
#
#             # Delete the unnecessary tabs. Loop backwards; prevents index shift.
#             for i in range(len(workbook.Sheets), 2, -1):
#                 sheet = workbook.Sheets(i)
#                 sheetname = sheet.Name
#
#                 if sheetname == tab_name:
#                     display_message(
#                         "INFO", f"Project sheet encountered ( {sheetname} )."
#                     )
#                     sheet.Name = f"{work_id}. {sheetname}"
#                     display_message("INFO", "Sheet renamed.")
#                 else:
#                     display_message("INFO", f"Deleting sheet : {sheetname} ... ")
#                     sheet.Delete()
#                     # shell.SendKeys("{ENTER}")
#                     display_message("SUCCESS", "Sheet deleted.")
#
#             # Save the changes back to the original file.
#             workbook.SaveAs(Filename=xlsx_path)
#             workbook.Close()
#             display_message("SUCCESS", f"Client CR file ( {base} ) purged.")
#
#         except Exception as e:
#             display_message(
#                 "ERROR", f"Failed to purge client CR file ( {base} ).", f"{e}"
#             )
#
#         finally:
#             excel_app.Quit()
#
#     try:
#         client = init_client()
#
#         # Terminate process if BoxClient is not created.
#         if not client:
#             raise Exception("Failed to create Box client.")
#
#         proj_cache = load_proj_cache(PROJ_CACHE)
#         proj_det = get_cached_proj_details(proj_cache)
#         work_id = proj_det["work_id"]
#         title_jp = proj_det["title_jp"]
#
#         feedback_files = get_box_entries(client, CR_FEEDBACK)
#         req_file_id = ""
#
#         for item in feedback_files:
#             item_name = item.name or ""
#
#             if "No." not in item_name:
#                 continue
#
#             work_id_range = get_range_from_name(item_name)
#
#             if int(work_id) in work_id_range:
#                 req_file_id = item.id
#
#                 display_message("SUCCESS", "Required Client CR file identified.")
#                 display_box_path(client, parse_box_url("file", req_file_id))
#                 break
#
#         if not req_file_id:
#             raise Exception("Failed to identify required file.")
#
#         dl_name = f"{datetime.now().strftime('%Y%m%d')} CR - {work_id}"
#         display_message(
#             "INFO",
#             f'Downloading required file as "{dl_name}.xlsx" ... ',
#         )
#
#         dl_dest_path = parse_pathname(PARENT_LOCAL, dl_name, "xlsx", "file")
#         dl_stat = dl_box_entry(client, req_file_id, dl_dest_path)
#
#         if dl_stat:
#             purge_xlsx(dl_dest_path, title_jp, work_id)
#
#     except Exception as e:
#         display_message("ERROR", "Failed to fetch CR file.", f"{e}")

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
                # "\n>>>  Rename [B]ox files (EN) ?"
                # "\n>>>  Revert B[O]x filenames ?"
                "\n>>>  [C]reate typesetting term folder ?"
                # "\n>>>  [M]ove PDF files to term folder ?"
                # "\n>>>  F[E]tch revision file/tab ?"
                "\n>>>  Fetc[H] translation file/s ?"
                "\n>>>  [D]ownload source files ?"
                # "\n>>>  Copy [T]ypesetting files to Revisions folder ?"
                "\n>>>  E[X]it and close this window ?"
            )

            resp = input(">>> ").upper()

            proper_resp = resp in ["C", "D", "H", "X"]

        if resp == "X":
            print("\n<=> Closing down ...")

            confirm_exit = True
        else:
            confirm_exit = False

            if resp == "C":
                create_term_tree()

            elif resp == "H":
                fetch_tl()

            elif resp == "D":
                fetch_data_files()
