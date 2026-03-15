from pathlib import Path
import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

root = Path(__file__).resolve().parents[2]   # adjust if needed
src = root                                   # or root / "src" if you use a src layout

files_to_document = [
    "ecowheataly_repast_model.py",
    "agents/farm.py",
    "agents/policy_maker.py",
    "agents/international_buyer.py",
    "agents/international_producer.py",
    "utils/utils.py",
]

paths_to_files=[Path(str(src)+'/'+tmpf) for tmpf in files_to_document]

for path in paths_to_files:
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
