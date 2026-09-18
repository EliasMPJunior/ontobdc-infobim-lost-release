# Data Gathered

`DataGatheredCapability` builds the semantic snapshot consumed by all later Surface transformations and writes it as a JSON-LD ETL state artifact.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.data_gathered` |
| Capability type | `TransformationCapability` |
| Resulting state | `data_gathered` |
| Implementation | [`data_gathered.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/surface/plugin/capability/transformation/data_gathered.py) |
| Primary artifact | `<container>/.__ontobdc__/etl/view/surface/__data_gathered__.jsonld` |

## Inputs and preconditions

The context must contain a resolvable `container_path`. The container's `container.ttl` must exist, parse as Turtle, and contain exactly one `obdc:DataContainer`. The publication descriptor is expected to be synchronized by the preceding state.

## Operation

The capability constructs one in-memory RDF graph:

1. Parse the container's own `container.ttl`.
2. Discover immediate child directories that contain an OntoBDC dataset metadata file and merge each `dataset.ttl` into the graph.
3. For each dataset entity, read its facade mapping and current workbook row. Current `Name` and `Description` values refresh `dcterms:title` and `dcterms:description`; other non-empty facade fields are materialized under their `mapsToProperty` predicate when that predicate has no value yet.
4. Declare `obdc:DataContainer` and `obdc:FileTree` as `obdc:SurfaceableEntity` in the gathered graph. This compensates for the fact that the capability does not load the external TBox files that normally carry those declarations.
5. Add one aggregate `obdc:FileTree` entity whose `obdc:filePath` values list the container-owned files.
6. Add one entity per file with title, path, optional format, byte size, container membership, and an RDF type selected by extension: `ImageFile`, `PdfFile`, `CsvFile`, or `GenericFile`.
7. Serialize the merged graph to JSON-LD and write the ETL artifact.

Individual file entities are deliberately not declared surfaceable. The main Surface shows the aggregate file tree and metadata; actual file content is opened only through the standalone file-viewer page after an explicit click.

## Result

The result contains `state_path`, `file_count`, `dataset_count`, and `resulting_state`. Unlike the HTML stages, this capability does not use or set `surface_path`.

## Satisfaction check

The state is satisfied when the expected ETL path is a file and its UTF-8 content parses as a JSON object or array. The check validates syntax and top-level shape; it does not repeat the graph's semantic constraints or compare the artifact with current source files.

## Failure behavior and tolerances

Invalid container metadata, multiple or missing container subjects, graph parse failures, and write failures abort execution. Dataset workbook enrichment is intentionally tolerant: failures while reading a dataset graph, facade, or workbook entity repository cause that optional enrichment slice to be skipped rather than aborting the complete Surface build.

## Tests

Unit tests: [`test_data_gathered.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/test/unit/surface/plugin/capability/transformation/test_data_gathered.py).

Unlike most capabilities in this pipeline, `DataGatheredCapability` has substantial logic of its own, so the suite mocks only the two collaborators that would otherwise require real filesystem-enumeration rules or a real Excel workbook (`ContainerDataPackageSynchronizer`, `DatasetEntityInstanceRepository`). `StorageBootstrap`'s path-join methods are exercised for real against hand-written Turtle fixtures placed at their exact resolved locations, and the RDF graph building and JSON-LD serialization run unmocked throughout.

**Pure helpers** (in-memory `Graph` or plain strings, no I/O):

| Test | Condition |
| --- | --- |
| `test_file_type_uri_classifies_by_extension` (7 cases) | `_file_type_uri()` maps `png`/`jpg`/`svg` to `ImageFile`, `pdf` to `PdfFile`, `csv` to `CsvFile`, and any other or empty extension to `GenericFile`. |
| `test_local_name_from_hash_fragment`, `test_local_name_from_trailing_slash_segment` | `_local_name()` extracts the fragment after `#`, or the last `/`-segment when there is no fragment. |
| `test_container_subject_returns_the_single_data_container` | `_container_subject()` returns the one `obdc:DataContainer` subject in the graph. |
| `test_container_subject_raises_when_none_present`, `test_container_subject_raises_when_more_than_one_present` | `_container_subject()` raises `ValueError` for zero or multiple `DataContainer` subjects. |
| `test_marks_data_container_and_file_tree_as_surfaceable` | `_add_surfaceable_declarations()` adds exactly the two expected `obdc:SurfaceableEntity` triples. |

**`check()`** (real `tmp_path`, no mocking):

| Test | Condition |
| --- | --- |
| `test_check_returns_true_for_a_valid_json_object_state_file`, `test_check_returns_true_for_a_valid_json_array_state_file` | `True` when the ETL artifact exists and parses as a JSON object or array. |
| `test_check_returns_false_when_state_file_is_missing` | `False` when the artifact does not exist. |
| `test_check_returns_false_for_invalid_json` | `False` when the file exists but is not valid JSON. |
| `test_check_returns_false_for_non_container_json_value` | `False` when the JSON parses but is neither an object nor an array (e.g. a bare string). |

**`execute()`** (real Turtle fixtures written to the exact paths `StorageBootstrap` resolves; `ContainerDataPackageSynchronizer.list_container_file_paths` and `DatasetEntityInstanceRepository` mocked):

| Test | Condition |
| --- | --- |
| `test_execute_with_zero_datasets_writes_state_and_returns_summary` | A container with no datasets and two files (one image, one PDF) produces a written JSON-LD artifact whose graph contains the `FileTree` entity, both typed file entities, and their `fileSize` triples; the returned summary reports `file_count == 2` and `dataset_count == 0`. |
| `test_execute_merges_dataset_triples_and_facade_field_values` | With one dataset present, the dataset's own entity is merged into the graph and its facade-mapped field (read from a mocked `DatasetEntityInstanceRepository.list_instances()` row) is materialized under the facade's `mapsToProperty` predicate; `dcterms:title`/`dcterms:description` are refreshed from the row's `Name`/`Description`. |
| `test_execute_tolerates_dataset_instance_repository_failure` | When `DatasetEntityInstanceRepository.list_instances()` raises (e.g. a missing datapackage), `execute()` still completes and simply omits the enriched field values for that entity, confirming the documented tolerance above. |
