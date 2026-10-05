# Market model

Market identity is explicit: event ID, market ID, condition ID, slug, outcome label, and outcome token ID are distinct. A Market retains its resolution contract (question, description, criteria/source when provided, close time, state, and resolved outcome). UTC timestamps distinguish exchange data from local ingestion.

Future snapshots also preserve provider, source timestamp, local collection
timestamp, resolution-rule vintage, related-market references, and order-book
state. A revised market description is a new vintage, not an overwrite of the
historical record used by a prior decision.
