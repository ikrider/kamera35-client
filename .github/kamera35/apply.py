"""Apply the Kamera35 branding to the pinned official RustDesk checkout."""
import argparse
import base64
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
config = json.loads((HERE/'config.json').read_text(encoding='utf-8'))


def replace(path, old, new):
    text = path.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{path}: expected one match for {old[:60]!r}, got {count}')
    path.write_text(text.replace(old,new), encoding='utf-8', newline='\n')


def settings_map(values):
    entries = ',\n'.join(f'        ("{k}".to_owned(), "{v}".to_owned())' for k,v in values.items())
    return 'RwLock::new(HashMap::from([\n'+entries+'\n    ]));'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve()
    if len(base64.b64decode(config['public_key'],validate=True)) != 32:
        raise ValueError('The server public key must decode to 32 bytes')
    cfg=root/'libs/hbb_common/src/config.rs'
    replace(cfg,'RwLock::new("RustDesk".to_owned());',f'RwLock::new("{config["app_name"]}".to_owned());')
    replace(cfg,'pub const RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"];',
        f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{config["server"]}"];')
    replace(cfg,'pub const RS_PUB_KEY: &str = "OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=";',
        f'pub const RS_PUB_KEY: &str = "{config["public_key"]}";')
    replace(cfg,'pub static ref DEFAULT_SETTINGS: RwLock<HashMap<String, String>> = Default::default();',
        'pub static ref DEFAULT_SETTINGS: RwLock<HashMap<String, String>> = '+settings_map({
        'custom-rendezvous-server':config['server'],'relay-server':config['relay'],'key':config['public_key']}))
    replace(cfg,'pub static ref DEFAULT_LOCAL_SETTINGS: RwLock<HashMap<String, String>> = Default::default();',
        'pub static ref DEFAULT_LOCAL_SETTINGS: RwLock<HashMap<String, String>> = '+settings_map({
        'lang':'ru','enable-check-update':'N','allow-auto-update':'N'}))

    common=root/'flutter/lib/common.dart'
    for old,new in [('0xFFEFEFF2','0xFFF3F6FB'),('0xFF0071FF','0xFF1F6BFF'),
                    ('0x770071FF','0x771F6BFF'),('0xAA0071FF','0xAA1F6BFF'),
                    ('0xFFCCCCCC','0xFFE3E9F2'),('0xFF00B6F0','0xFF1E5BD8'),
                    ('0xFF2C8CFF','0xFF1F6BFF')]:
        text=common.read_text(encoding='utf-8')
        if old not in text: raise RuntimeError(f'Color {old} missing')
        common.write_text(text.replace(old,new),encoding='utf-8',newline='\n')
    titlebar=root/'flutter/lib/desktop/widgets/titlebar_widget.dart'
    for old,new in [('0xFF0C6AF6','0xFF1E5BD8'),('0xFF0583EA','0xFF1E5BD8'),('0xFF0697EA','0xFF1F6BFF')]:
        replace(titlebar,old,new)
    replace(root/'flutter/lib/desktop/pages/desktop_home_page.dart','0xFF2F65BA','0xFF1E5BD8')

    rc=root/'flutter/windows/runner/Runner.rc'
    replace(rc,'"FileDescription", "RustDesk Remote Desktop"','"FileDescription", "Kamera35 Remote Support"')
    replace(rc,'"ProductName", "RustDesk"','"ProductName", "Kamera35"')
    # Retain upstream copyright and the visible "Powered by RustDesk" attribution.
    for name in ('logo.png','logo_light.png','logo_dark.png','icon.png','icon.ico'):
        shutil.copyfile(HERE/name,root/'flutter/assets'/name)
    for target in ('res/icon.ico','res/tray-icon.ico','flutter/windows/runner/resources/app_icon.ico'):
        shutil.copyfile(HERE/'icon.ico',root/target)
    print('Applied Kamera35 brand, public server key and ru language defaults.')


if __name__=='__main__': main()
