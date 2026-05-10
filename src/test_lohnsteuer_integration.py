"""
Unit-Tests für PAP-Parser.

Validiert:
- XML-Dateiladung
- Tarifwerte-Extraktion
- Lohnsteuer-Berechnung
"""

import unittest
import sys
from pathlib import Path

# Importiere Parser
try:
    from lohnsteuer_integration import PAPParser, Tarifwerte
except ImportError:
    # Fallback für lokale Tests
    sys.path.insert(0, str(Path(__file__).parent))
    from lohnsteuer_integration import PAPParser, Tarifwerte


class TestPAPParser(unittest.TestCase):
    """Test PAP Parser Funktionalität."""
    
    @classmethod
    def setUpClass(cls):
        """Setup vor allen Tests."""
        try:
            cls.parser = PAPParser()
            cls.parser_available = True
        except FileNotFoundError as e:
            print(f"⚠️  PAP-XML nicht gefunden: {e}")
            cls.parser_available = False
    
    def test_parser_initialization(self):
        """Test: Parser Initialisierung."""
        self.assertTrue(self.parser_available, "PAP XML-Verzeichnis muss existieren")

    def test_extract_tarifwerte_2026(self):
        """Test: Extrahiere Tarifwerte für 2026."""
        if not self.parser_available:
            self.skipTest("XML-Dateien nicht verfügbar")

        tarifwerte = self.parser.extract_tarifwerte(2026)

        # Validiere Tarifwerte
        self.assertIsNotNone(tarifwerte)
        self.assertEqual(tarifwerte.jahr, 2026)
        self.assertGreater(tarifwerte.grundfreibetrag, 0)
        self.assertIsNotNone(tarifwerte.steuersaetze)
        self.assertIsNotNone(tarifwerte.grenzwerte)

        print(f"✅ Tarifwerte 2026 geladen:")
        print(f"   Grundfreibetrag: {tarifwerte.grundfreibetrag}€")
        print(f"   Steuersätze: {tarifwerte.steuersaetze}")
    
    def test_lohnsteuer_calculation_simple(self):
        """Test: Einfache Lohnsteuer-Berechnung."""
        if not self.parser_available:
            self.skipTest("XML-Dateien nicht verfügbar")

        # Test: Brutto 3000€/Monat
        result = self.parser.berechne_lohnsteuer(
            bruttolohn=3000,
            jahr=2026,
            steuerkl=1,
            lzz=2  # Monat
        )

        # Validiere Rückgabewerte
        self.assertIsNotNone(result)
        self.assertIn("brutto", result)
        self.assertIn("netto", result)
        self.assertIn("lohnsteuer", result)

        # Netto < Brutto (Steuern abgezogen)
        self.assertLess(result["netto"], result["brutto"])

        # Alle Werte >= 0
        self.assertGreaterEqual(result["lohnsteuer"], 0)
        self.assertGreaterEqual(result["soli"], 0)

        print(f"✅ Berechnung 3000€ Brutto (Monat, SK1):")
        for key, val in result.items():
            print(f"   {key}: {val}")
    
    def test_lohnsteuer_zero_income(self):
        """Test: Null-Einkommen."""
        if not self.parser_available:
            self.skipTest("XML-Dateien nicht verfügbar")
        
        result = self.parser.berechne_lohnsteuer(
            bruttolohn=0,
            jahr=2026,
            steuerkl=1,
            lzz=2
        )
        
        self.assertEqual(result["netto"], 0)
        self.assertEqual(result["lohnsteuer"], 0)
        print("✅ Null-Einkommen: Korrekt")
    
    def test_lohnsteuer_low_income(self):
        """Test: Grundfreibetrag-Bereich."""
        if not self.parser_available:
            self.skipTest("XML-Dateien nicht verfügbar")

        # Monatlich unter Grundfreibetrag
        result = self.parser.berechne_lohnsteuer(
            bruttolohn=500,
            jahr=2026,
            steuerkl=1,
            lzz=2
        )

        # Steuer sollte 0 oder minimal sein
        self.assertLessEqual(result["lohnsteuer"], 50)
        print(f"✅ Niedriges Einkommen (500€): Lohnsteuer {result['lohnsteuer']}€")


class TestTarifwerte(unittest.TestCase):
    """Test Tarifwerte-Datenklasse."""
    
    def test_tarifwerte_to_dict(self):
        """Test: Tarifwerte.to_dict()."""
        from decimal import Decimal
        
        tarifwerte = Tarifwerte(
            jahr=2026,
            grundfreibetrag=Decimal("120.84"),
            steuersaetze={"normal": Decimal("0.42")},
            grenzwerte={"max": Decimal("1000.00")},
            zusaetze={"soli": Decimal("0.055")}
        )
        
        result_dict = tarifwerte.to_dict()
        
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict["jahr"], 2026)
        self.assertIsInstance(result_dict["grundfreibetrag"], float)
        print(f"✅ Tarifwerte.to_dict() OK: {result_dict['grundfreibetrag']}€")


def run_tests():
    """Führe alle Tests aus."""
    print("\n" + "="*60)
    print("🧪 Lohnsteuer-Integration Tests")
    print("="*60 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Lade Tests
    suite.addTests(loader.loadTestsFromTestCase(TestPAPParser))
    suite.addTests(loader.loadTestsFromTestCase(TestTarifwerte))
    
    # Führe Tests aus
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Zusammenfassung
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("✅ ALLE TESTS BESTANDEN")
    else:
        print(f"❌ FEHLER: {len(result.failures)} Fehler, {len(result.errors)} Exceptions")
    print("="*60 + "\n")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
