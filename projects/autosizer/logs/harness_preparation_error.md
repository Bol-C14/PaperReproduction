Before simulation attempt 3, the first repaired-deck preparation failed with
`ValueError: substring not found`: YAML strips common template indentation, while
the local patch matcher expected four spaces. No ngspice process was launched and
no attempt was allocated. The matcher was corrected to ignore leading indentation.
The original templates and the frozen circuit/specifications were not changed.
