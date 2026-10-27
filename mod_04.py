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
    display_message,
    display_path_desc,
    ensure_path_exists,
    expand_path,
    get_term_details,
    hor_bar,
    load_proj_cache,
    parse_pathname,
    show_table,
    welcome_sequence,
)

# Module variables
mod_name = "Box API Operations"
mod_ver = "1"
date = "27 Oct 2026"
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

        if sources:
            dl_box_entry(client, sources, zip_dest_path)
        else:
            # In case of inconsistent folder structure.
            display_message("ERROR", f"Typesetting data not found.  Verify Box folder : {parent}")

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
            target = find_box_entry_by_name(
                client, parent, "folder", folder_name, True
            )

            if target:  # source becomes parent.
                parent = parse_box_url("folder", target.id)
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

            box_delay(1)    #1-sec delay between files.

    except Exception as e:  # noqa: BLE001
        display_message("ERROR", "Failed to fetch translation document.", f"{e}")
        return


def create_term_tree() -> None:
    try:
        chapter_urls = {}

        display_message("WARN", "Ensure term, and \"03\" folders exist.")
        pre_folders_exist = input("[C]ontinue or [Q]uit ?")

        if pre_folders_exist.upper() == "Q":
            display_message("WARN", "Terminating")
            return

        cache = load_proj_cache(PROJ_CACHE)
        sole_id, proj_name, term, chapters = get_term_details(cache)

        client = init_client()

        if not client:
            display_message("ERROR", "Failed to create BoxClient object.")
            return

        parent = BOX_PARENT     #Initialise parent to project parent Box folder.

        # Typeset files for checking to be loaded on "03"
        # parent >> term >> 03 >> proj_name >> chapters
        for i, folder_name in enumerate([term, "03", sole_id, chapters]):
            if isinstance(folder_name, str):
                hor_bar(100)

                target = find_box_entry_by_name(
                    client, parent, "folder", folder_name, True
                )

                if target:
                    # target becomes parent
                    parent = parse_box_url("folder", target.id)
                elif i == 2:    # i=3 "sole_id" might not be present; term and "03" are populated by template
                    box_delay(2)    #2-sec delay
                    folder_id = ensure_box_folder_exists(client, parent, proj_name)

                    if folder_id:
                        # created title folder becomes parent
                        parent = parse_box_url("folder", folder_id)

            elif isinstance(folder_name, list):
                for sibling in folder_name:
                    hor_bar(100)
                    box_delay(2)    #2-sec delay between folder creation
                    sibling_id = ensure_box_folder_exists(client, parent, f"{int(sole_id):010}_{lang_iso_2}_{sibling}")
                    chapter_urls[sibling] = parse_box_url("folder", sibling_id)

        hor_bar(100)

        show_table(
            f"New Box Folders for Term{term} : {proj_name}",
            [3, 10, 50],
            ["", "Chapters", "Folder URL"],
            [[i + 1, k, v] for i, (k, v) in enumerate(chapter_urls.items())],
        )

        box_delay(2)    #2-sec delay between Box folder creation

        return

    except Exception as e:  # noqa: BLE001
        display_message("ERROR", "Failed to create term tree in Box.", f"{e}")
        return

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
