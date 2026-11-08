"""Editionen sind Bereitstellungsprofile, keine Berechtigungsnachweise."""
import platform
import sys
from pathlib import Path
from .models import SkillAuditResult

EDITIONS = {
    'codex': {'name': 'codex-skill-auditor', 'version': '1.1.0',
              'surfaces': {'cli': 'P-CX', 'app': 'P-CX', 'ide': 'P-CX'}, 'default': 'cli'},
    'claude-code': {'name': 'skill-auditor', 'version': '2.6.0',
                    'surfaces': {'cli': 'P-CC'}, 'default': 'cli'},
    'claude-desktop': {'name': 'skill-auditor-desktop', 'version': '1.1.0',
                       'surfaces': {'desktop-chat': 'P-DT', 'web': 'P-WEB', 'cowork': 'P-CW'}, 'default': 'desktop-chat'},
}


def capability_report(edition, surface=None):
    from . import SCANNER_VERSION
    config = EDITIONS[edition]
    surface = surface or config['default']
    profile = config['surfaces'][surface]
    return {'edition': config['name'], 'edition_version': config['version'], 'core_version': SCANNER_VERSION,
            'profile': profile, 'surface': surface, 'surface_evidence': 'caller_declared',
            'os': platform.system(), 'python': platform.python_version(),
            'minimum_python': '3.11', 'runtime_candidate': sys.version_info >= (3, 11),
            'guard_implementation_available': sys.platform == 'win32' or sys.platform.startswith('linux'),
            'guard_active': False, 'scanner_allowed_by_profile': profile != 'P-CW',
            'inventory_available': edition != 'claude-desktop',
            'cowork_device_scanner': 'deferred', 'installation_performed': False,
            'limitations': 'Keine Erkennung der echten App-Sitzung, kein Zugriffs- oder Plattformtest; Wächter erst im Lauf aktiv.'}


def apply_profile(result, edition, surface):
    config = EDITIONS[edition]
    result.execution.profile = config['surfaces'][surface]
    result.execution.surface = surface
    result.input_details['edition'] = {'name': config['name'], 'version': config['version'],
                                      'surface_evidence': 'caller_declared'}
    return result


def no_scan_result(path, edition, surface):
    # Do not stat/resolve/list/open the supplied object here.
    result = SkillAuditResult(str(path), Path(path).name or 'Prüfobjekt')
    result.execution.scan_mode = 'content_review_only'
    result.execution.scanner_executed = False
    reason = ('Cowork-Geräte-Scanner vorläufig zurückgestellt; keine automatische Ausweichumgebung'
              if surface == 'cowork' else 'Scanner ausdrücklich nicht ausgeführt; Inhaltsprüfung durch Menschen/KI steht aus')
    result.skipped_files = [{'file': str(path), 'reason': reason}]
    return apply_profile(result, edition, surface)
