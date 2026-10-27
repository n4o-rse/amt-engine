# Third-party libraries of the Explorer

These files are copied unchanged from the packages below, so that the Explorer
loads nothing from a CDN: no third party sees who opens it, and it works offline.
They are not generated. To update one, replace the files and change the version here.

| Folder | Package | Version | Licence | Used for |
|---|---|---|---|---|
| `n3/` | [N3.js](https://github.com/rdfjs/N3.js) (`browser/n3.min.js`) | 1.17.2 | MIT | parsing Turtle |
| `vis/` | [vis](https://github.com/almende/vis) (`dist/vis.min.js`, `vis.min.css`, `img/`) | 4.20.0 | MIT or Apache-2.0 | drawing the graph |
| `jquery/` | [jQuery](https://jquery.com) (`jquery.min.js`) | 1.12.4 | MIT | Materialize, jQuery UI |
| `jquery-ui/` | [jQuery UI](https://jqueryui.com) (`jquery-ui.min.js`, `.css`, `images/`) | 1.12.1 | MIT | dialogs and widgets |
| `materialize/` | [Materialize](https://github.com/Dogfalo/materialize) (`css`, `js`, Roboto fonts) | 0.100.2 | MIT | layout, buttons |
| `material-icons/` | [Material Icons](https://github.com/marella/material-icons) (`iconfont/material-icons.woff2`, `.woff`) | 1.13.12 | Apache-2.0 | the icons of the toolbar |

The Explorer page, `../explorer/index.html`, loads them from here; `tests/test_offline.py` checks that no page
and no stylesheet of `docs/` references a file on another server.
