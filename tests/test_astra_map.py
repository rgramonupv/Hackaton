"""Offline acceptance checks of Opus's unchanged app; no production database writes.

Run from the repository root: python -m unittest discover -s tests -v
AppTest injects component return values: it is NOT a browser click test.
"""
import gc
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import streamlit as st
from streamlit.testing.v1 import AppTest

import data
import db
import model
from ui.astra_map import map_component_key, reset_proposal

ROOT = Path(__file__).resolve().parents[1]


def numeric(value):
    """The demo formats integer counts with either English or Spanish grouping."""
    return float(value.replace(",", "").replace(".", "").replace("€", "").strip())


def russafa():
    barrio = next(b for b in data.load_barrios() if b["properties"]["nombre"] == "RUSSAFA")
    ring = barrio["geometry"]["coordinates"][0]
    lat0 = sum(p[1] for p in ring) / len(ring)
    blocks = model.blocks_from_features(data.load_layer_in_barrio("manzanas", barrio), lat0)
    benches = [tuple(reversed(f["geometry"]["coordinates"][:2]))
               for f in data.load_layer_in_barrio("bancos", barrio)]
    return barrio, lat0, blocks, benches, model.estimate_population(blocks, 150, 22)


class CoverageTests(unittest.TestCase):
    def test_empty_inputs_and_zero_population(self):
        self.assertEqual(model.coverage([], np.array([]), [], 75, 39.46), 0)
        blocks = [{"lat": 39.46, "lon": -0.37, "area": 0}]
        np.testing.assert_array_equal(model.estimate_population(blocks, 150, 22), [0])
        np.testing.assert_array_equal(model.covered_mask(blocks, [], 75, 39.46), [False])

    def test_distance_boundary_and_no_double_count(self):
        blocks = [{"lat": 0.0, "lon": 0.0, "area": 1}]
        benches = [(0.0, 75 / model.M_PER_DEG_LAT)]
        self.assertEqual(model.coverage(blocks, np.array([33]), benches, 75, 0), 33)
        self.assertEqual(model.coverage(blocks, np.array([33]), benches, 74.99, 0), 0)
        self.assertEqual(model.coverage(blocks, np.array([33]), benches * 2, 75, 0), 33)

    def test_real_cached_data_radius_monotonic_and_new_bench_gain(self):
        with patch("requests.post", side_effect=AssertionError("Network forbidden in tests")):
            _, lat0, blocks, benches, elderly = russafa()
        values = [model.coverage(blocks, elderly, benches, r, lat0) for r in range(25, 301, 25)]
        self.assertEqual(values, sorted(values))
        self.assertTrue(all(0 <= v <= elderly.sum() for v in values))
        uncovered = np.flatnonzero(~model.covered_mask(blocks, benches, 75, lat0))
        self.assertGreater(len(uncovered), 0)
        b = blocks[uncovered[0]]
        before = model.coverage(blocks, elderly, benches, 75, lat0)
        after = model.coverage(blocks, elderly, benches + [(b["lat"], b["lon"])], 75, lat0)
        self.assertGreater(after, before)

    def test_population_controls_scale_estimates(self):
        _, _, blocks, _, elderly = russafa()
        np.testing.assert_allclose(model.estimate_population(blocks, 300, 22), elderly * 2)
        np.testing.assert_allclose(model.estimate_population(blocks, 150, 11), elderly / 2)


class MapLifecycleTests(unittest.TestCase):
    def test_reset_changes_component_identity_and_preserves_other_fields(self):
        state = {"new_benches": [(39.46, -0.37)], "new_trees": [(39.45, -0.36)],
                 "last_click": {"lat": 39.46, "lng": -0.37}, "voter": "Ana", "radius": 75}
        key = map_component_key("RUSSAFA", state)
        reset_proposal(state)
        self.assertNotEqual(map_component_key("RUSSAFA", state), key)
        self.assertEqual(state["new_benches"], [])
        self.assertEqual(state["new_trees"], [])
        self.assertIsNone(state["last_click"])
        self.assertEqual((state["voter"], state["radius"]), ("Ana", 75))
        self.assertNotEqual(map_component_key("RUSSAFA", state), map_component_key("BENICALAP", state))
        next_key = map_component_key("RUSSAFA", state)
        reset_proposal(state)
        self.assertNotEqual(map_component_key("RUSSAFA", state), next_key)


class TemporaryDatabaseCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="valencia-astra-test-")
        self.addCleanup(self.temp.cleanup)
        db_patch = patch.object(db, "DB_PATH", Path(self.temp.name) / "proposals.db")
        db_patch.start()
        self.addCleanup(db_patch.stop)
        # sqlite's connection context commits but does not close. Collect released
        # connections before deleting our temporary file on Windows; do not patch db.
        self.addCleanup(gc.collect)

    def proposal(self, title="A", barrio="RUSSAFA", before=100, after=140, cost=800):
        return db.save_proposal(barrio, title, "Ana", [(39.46, -0.37)], [], cost,
                                before, after, {"radius": 75})


class VotingTests(TemporaryDatabaseCase):
    def test_two_neighbours_one_vote_each_and_independent_proposals(self):
        first, second = self.proposal("A"), self.proposal("B")
        self.assertTrue(db.vote(first, "Ana"))
        self.assertFalse(db.vote(first, "Ana"))
        self.assertTrue(db.vote(first, "Luis"))
        self.assertTrue(db.vote(second, "Ana"))
        self.assertEqual([(p["id"], p["votes"]) for p in db.ranking("RUSSAFA")],
                         [(first, 2), (second, 1)])

    def test_ranking_order_filter_and_saved_impact(self):
        first, second = self.proposal("A"), self.proposal("B", cost=1200, after=160)
        self.proposal("Other", barrio="OTHER")
        db.vote(second, "Ana")
        db.vote(second, "Luis")
        rows = db.ranking("RUSSAFA")
        self.assertEqual([p["id"] for p in rows], [second, first])
        self.assertEqual(rows[0]["cost"] / (rows[0]["elderly_after"] - rows[0]["elderly_before"]), 20)
        self.assertEqual(json.loads(rows[0]["benches"]), [[39.46, -0.37]])
        self.assertEqual(json.loads(rows[0]["params"]), {"radius": 75})


class ExistingAppTests(TemporaryDatabaseCase):
    """Real app/model/db execution; only the Folium browser event boundary is mocked."""
    def setUp(self):
        super().setUp()
        st.cache_data.clear()
        self.addCleanup(st.cache_data.clear)
        network = patch("requests.post", side_effect=AssertionError("Network forbidden in tests"))
        network.start()
        self.addCleanup(network.stop)
        self.event = {"last_clicked": None}
        self.maps = []

        def component(m, **kwargs):
            self.maps.append(m)
            return self.event

        component_patch = patch("streamlit_folium.st_folium", side_effect=component)
        component_patch.start()
        self.addCleanup(component_patch.stop)
        self.app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
        self.run_app()

    def run_app(self):
        self.app.run()
        self.assertEqual(len(self.app.exception), 0, str(self.app.exception))

    def metric(self, label):
        aliases = {"Coste de la propuesta": "Coste",
                   "€ por mayor beneficiado": "Coste por persona mayor beneficiada"}
        if label.startswith("Mayores a ≤"):
            aliases[label] = label.replace("Mayores a ≤", "Mayores con banco a ≤").replace(" de un banco", "")
        return next(m for m in self.app.tabs[0].metric if m.label in (label, aliases.get(label)))

    def button(self, text):
        aliases = {"Deshacer todo": "Quitar todo lo añadido", "Publicar para votación": "Publicar propuesta"}
        return next(b for b in self.app.button if text in b.label or b.label == aliases.get(text))

    def select_tree(self):
        self.app.radio[0].set_value(next(o for o in self.app.radio[0].options if "árbol" in o.lower()))

    def add_uncovered_bench(self):
        _, lat0, blocks, benches, _ = russafa()
        b = blocks[np.flatnonzero(~model.covered_mask(blocks, benches, 75, lat0))[0]]
        self.event = {"last_clicked": {"lat": b["lat"], "lng": b["lon"]}}
        self.run_app()

    def test_startup_real_layers_counts_and_coordinate_order(self):
        if any(m.label == "Bancos existentes" for m in self.app.metric):
            for label, count in [("Bancos existentes", "193"), ("Árboles existentes", "522"),
                                 ("Parques y jardines", "13"), ("Manzanas", "81")]:
                self.assertEqual(self.metric(label).value, count)
        else:
            counts = " ".join(m.value for m in self.app.markdown)
            for expected in ("193 bancos", "522 árboles", "13 parques", "81 manzanas"):
                self.assertIn(expected, counts)
        _, _, _, benches, _ = russafa()
        circles = [c for c in self.maps[-1]._children.values() if c.__class__.__name__ == "CircleMarker"]
        self.assertEqual(len(circles), 193 + 522)
        self.assertEqual(circles[-193].location, list(benches[0]))
        self.assertRegex(self.maps[-1].get_root().render(), r"mayores \(est[.)i]")

    def test_bench_event_recalculates_and_repeated_return_does_not_duplicate(self):
        before = numeric(self.metric("Mayores a ≤ 75 m de un banco").value)
        self.add_uncovered_bench()
        self.assertEqual(len(self.app.session_state["new_benches"]), 1)
        self.assertEqual(self.metric("Coste de la propuesta").value, "800 €")
        self.assertGreater(numeric(self.metric("Mayores a ≤ 75 m de un banco").value), before)
        self.run_app()
        self.app.slider[0].set_value(150)
        self.run_app()
        self.assertEqual(len(self.app.session_state["new_benches"]), 1)
        self.assertGreaterEqual(numeric(self.metric("Mayores a ≤ 150 m de un banco").value), before)

    def test_tree_event_cost_changes_and_zero_benefit(self):
        before = self.metric("Mayores a ≤ 75 m de un banco").value
        self.select_tree()
        self.event = {"last_clicked": {"lat": 39.462, "lng": -0.373}}
        self.run_app()
        self.assertEqual(len(self.app.session_state["new_trees"]), 1)
        self.assertEqual(self.metric("Coste de la propuesta").value, "400 €")
        self.assertEqual(self.metric("Mayores a ≤ 75 m de un banco").value, before)
        self.assertEqual(self.metric("€ por mayor beneficiado").value, "—")
        self.app.number_input[1].set_value(600)
        self.run_app()
        self.assertEqual(self.metric("Coste de la propuesta").value, "600 €")
        self.assertEqual(len(self.app.session_state["new_trees"]), 1)

    def test_mixed_cost_controls_and_undo(self):
        self.add_uncovered_bench()
        self.select_tree()
        self.event = {"last_clicked": {"lat": 39.462, "lng": -0.373}}
        self.run_app()
        self.assertEqual(numeric(self.metric("Coste de la propuesta").value), 1200)
        self.app.number_input[0].set_value(1000)
        self.run_app()
        self.assertEqual(numeric(self.metric("Coste de la propuesta").value), 1400)
        self.button("Deshacer todo").click()
        self.run_app()
        self.assertEqual(self.app.session_state["new_benches"], [])
        self.assertEqual(self.app.session_state["new_trees"], [])
        self.assertEqual(self.metric("Coste de la propuesta").value, "0 €")

    def test_save_and_ranking_ui_with_two_neighbours(self):
        other = self.proposal("B", cost=1200, after=160)
        self.add_uncovered_bench()
        self.app.text_input[0].set_value("A")
        self.button("Publicar para votación").click()
        self.run_app()
        saved = next(p for p in db.ranking() if p["title"] == "A")
        self.assertEqual(saved["cost"], 800)
        self.assertGreater(saved["elderly_after"], saved["elderly_before"])
        self.app.button(key=f"vote_{saved['id']}").click()
        self.run_app()
        self.app.button(key=f"vote_{saved['id']}").click()
        self.run_app()
        self.assertEqual(db.ranking()[0]["votes"], 1)
        self.app.selectbox[1].set_value("Luis")
        self.run_app()
        self.app.button(key=f"vote_{saved['id']}").click()
        self.run_app()
        self.assertEqual([(p["id"], p["votes"]) for p in db.ranking()], [(saved["id"], 2), (other, 0)])
        headings = [m.value for m in self.app.markdown if m.value.startswith("**#")]
        if headings:
            self.assertTrue(headings[0].startswith("**#1 A**"))
            self.assertTrue(any(m.label == "€ / beneficiado" for m in self.app.metric))
        else:
            rows = [m.value for m in self.app.markdown if 'class="rank-row"' in m.value]
            self.assertIn('class="rank-title">A', rows[0])
            self.assertIn('2 votos.', rows[0])
            self.assertIn('800 €', rows[0])
            self.assertIn('€ por persona', rows[0])
        self.assertTrue(any("población" in c.value.lower() and "estimadas" in c.value for c in self.app.caption))

    def test_known_issue_save_must_refresh_empty_draft_metrics(self):
        """Known app.py issue: metrics are rendered before save clears the draft."""
        self.add_uncovered_bench()
        self.button("Publicar para votación").click()
        self.run_app()
        self.assertEqual(self.app.session_state["new_benches"], [])
        self.assertEqual(self.metric("Coste de la propuesta").value, "0 €")

    def test_known_issue_ca5_ranking_must_show_total_covered(self):
        """CA5 requires covered elderly; current UI shows only the incremental gain."""
        self.proposal()
        self.run_app()
        metrics = [f"{m.label} {m.value}" for m in self.app.tabs[1].metric]
        content = " ".join(metrics + [m.value for m in self.app.tabs[1].markdown])
        # Saved fixture: before=100, after=140, gain=40. Require the total itself,
        # not a particular label spelling or a coincidental '+40' gain.
        self.assertRegex(content, r"(?<!\d)140(?!\d)")


if __name__ == "__main__":
    unittest.main()
