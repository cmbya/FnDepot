import unittest
from asset_selection import choose_versioned_asset
from update_fndepot import choose_fpk_asset


def asset(name):
    return {'name': name}


class SelectionTests(unittest.TestCase):
    def select(self, names, prefix, preferred=None):
        return choose_fpk_asset({'assets': [asset(n) for n in names]}, preferred, prefix)['name']

    def test_ekko_same_day(self):
        for names in [['Ekko-0.8.15-x86.fpk', 'Ekko-0.8.16-x86.fpk'], ['Ekko-0.8.16-x86.fpk', 'Ekko-0.8.15-x86.fpk']]:
            self.assertEqual(self.select(names, 'Ekko-'), 'Ekko-0.8.16-x86.fpk')

    def test_numeric_not_lexical(self):
        self.assertEqual(self.select(['Ekko-0.8.9-x86.fpk', 'Ekko-0.8.16-x86.fpk'], 'Ekko-'), 'Ekko-0.8.16-x86.fpk')
        self.assertEqual(self.select(['CLIProxyAPI_8.0.55_fnOS_x86.fpk', 'CLIProxyAPI_8.0.56_fnOS_x86.fpk'], 'CLIProxyAPI_'), 'CLIProxyAPI_8.0.56_fnOS_x86.fpk')
        self.assertEqual(self.select(['MeTube_2026.09.28_fnOS_x86.fpk', 'MeTube_2026.11.01_fnOS_x86.fpk'], 'MeTube_'), 'MeTube_2026.11.01_fnOS_x86.fpk')

    def test_architecture_and_prefix(self):
        self.assertEqual(self.select(['Ekko-9.0.0-arm64.fpk', 'Ekko-0.8.16-x86.fpk', 'Other-99.0.0-x86.fpk'], 'Ekko-'), 'Ekko-0.8.16-x86.fpk')

    def test_explicit_preference(self):
        self.assertEqual(self.select(['Ekko-0.8.15-x86.fpk', 'Ekko-0.8.16-x86.fpk'], 'Ekko-', 'Ekko-0.8.15-x86.fpk'), 'Ekko-0.8.15-x86.fpk')
        self.assertIsNone(choose_fpk_asset({'assets':[asset('Ekko-0.8.16-x86.fpk')]}, 'missing.fpk', 'Ekko-'))

    def test_unknown_or_absent_prefix_keeps_old_order(self):
        names = ['Ekko-latest-x86.fpk', 'Ekko-0.8.16-x86.fpk']
        self.assertEqual(self.select(names, 'Ekko-'), names[0])
        self.assertEqual(self.select(['A-1.0.0-x86.fpk', 'B-9.0.0-x86.fpk'], None), 'A-1.0.0-x86.fpk')
        self.assertIsNone(choose_fpk_asset({'assets': []}, asset_prefix='Ekko-'))
        self.assertIsNone(choose_fpk_asset({'assets':[asset('Other-1.0.0.fpk')]}, asset_prefix='Ekko-'))

    def test_equal_versions_stable(self):
        first, second = asset('Ekko-1.2.0-x86.fpk'), asset('Ekko-1.2-x86.fpk')
        self.assertIs(choose_versioned_asset([first, second], 'Ekko-', lambda _: 10), first)


if __name__ == '__main__':
    unittest.main()
