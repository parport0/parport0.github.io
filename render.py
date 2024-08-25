import os
import markdown

html_header = """<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:ital@0;1&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Reddit+Mono&display=swap');
body {
  font-family: "Noto Sans", sans-serif;
  font-optical-sizing: auto;
  font-weight: 400;
  font-style: normal;
  font-variation-settings: "wdth" 100;
}
code {
  font-family: "Reddit Mono", monospace;
  font-optical-sizing: auto;
  font-weight: 400;
  font-style: normal;
  color: hsl(220deg 73% 24%);
  overflow-wrap: break-word;
}
pre {
  overflow-x: scroll;
  background-color: #ececf8;
}
a:link, a:visited {
  color: hsl(220deg 60% 40%);
}
a.headerlink {
  text-decoration: none;
  margin-left: 0.5em;
  color: hsl(360deg, 0%, 77%)
}
a.headerlink:hover {
  text-decoration: underline;
  color: hsl(360deg, 0%, 43%)
}
</style>
</head>
<body>
"""

html_footer = """
</body>
</html>
"""

def to_html(name: str) -> str:
    return name[:-3] + ".html"

def md_to_title(md: markdown.Markdown) -> str:
    return md.Meta['date'][0] + ". " + md.Meta['title'][0]

def wrap_html(html: str) -> str:
    return html_header + html + html_footer

toc_text = ""
markdown_exts = ['fenced_code', 'smarty', 'meta', 'toc']
markdown_ext_configs = { 'toc': { 'permalink': '#' }}
md = markdown.Markdown(extensions=markdown_exts, extension_configs=markdown_ext_configs)

for file in os.scandir():
    if file.is_file() and file.name.endswith('.md'):
        with open(file.name, "r", encoding="utf-8") as input_file:
            md_text = input_file.read()
        html = md.reset().convert(md_text)

        # TOC
        # Run this while the metadata is still there --- before the next convert()
        toc_text += "- [" + md_to_title(md) + "](/" + to_html(file.name) + ")\n"

        # Page headers
        # The 'meta' extension does not allow parsing metadata without
        # converting the text into html.
        # It also doesn't allow using fields from meta in the result.
        # Render the title of the page independently, I guess
        title_md = "# " + md_to_title(md) + "\n"
        up_md = "[(index)](/)\n"
        html = md.reset().convert(up_md + title_md) + html
        html = wrap_html(html)

        # "errors" and "encoding" -- from https://python-markdown.github.io/reference/
        with open(to_html(file.name), "w", encoding="utf-8", errors="xmlcharrefreplace") as output_file:
            output_file.write(html)

toc_html = md.reset().convert(toc_text)
toc_html = wrap_html(toc_html)
with open("index.html", "w", encoding="utf-8", errors="xmlcharrefreplace") as output_file:
    output_file.write(toc_html)
