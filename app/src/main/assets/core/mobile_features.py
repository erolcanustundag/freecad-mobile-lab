# SPDX-License-Identifier: LGPL-2.1-or-later
"""Portable upstream FeaturePython example; metadata, not a geometric solid."""
import re


class QuantityDriver:
    def __init__(self, obj, source, input_property, factor):
        self.loads({"version": 1, "input_property": input_property})
        obj.addProperty("App::PropertyLink", "Source", "Script")
        obj.addProperty("App::PropertyFloat", "Factor", "Script")
        obj.addProperty("App::PropertyLength", "Output", "Script")
        obj.Source = source
        obj.Factor = factor
        obj.Proxy = self

    @staticmethod
    def validate(state):
        if not isinstance(state, dict) or set(state) != {"version", "input_property"} or state["version"] != 1:
            raise ValueError("Unsupported QuantityDriver state")
        name = state["input_property"]
        if not isinstance(name, str) or len(name) > 80 or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name):
            raise ValueError("Invalid driver property")

    def dumps(self):
        return {"version": 1, "input_property": self.input_property}

    def loads(self, state):
        self.validate(state)
        self.input_property = state["input_property"]

    def execute(self, obj):
        if obj.Source is None:
            raise ValueError("QuantityDriver has no source")
        obj.Output = getattr(obj.Source, self.input_property) * obj.Factor

    def onDocumentRestored(self, obj):
        obj.touch()
