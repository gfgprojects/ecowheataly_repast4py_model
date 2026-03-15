from pathlib import Path
import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

root = Path(__file__).resolve().parents[2]   # adjust if needed
src = root                                   # or root / "src" if you use a src layout
print(src)
for path in sorted(src.rglob("*.py")):
    #print(path)
    # Skip unwanted folders
    if any(part in {"__pycache__", ".venv", "venv", "site-packages", "docs","brightway2","data_from_2020_census","dati_adele","output","utils"} for part in path.parts):
        continue

    module_path = path.relative_to(src).with_suffix("")
    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("api", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__main__":
        continue

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}\n")

    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(root))

with mkdocs_gen_files.open("api/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
