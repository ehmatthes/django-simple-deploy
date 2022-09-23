# Read file
with open('supporting_platforms.md') as f:
    lines = f.readlines()

# Generate toc
toc_string = ''

for line in lines:
    if '### ' in line:
        raw_header = line.removeprefix('### ')

        # Replace special characters in link strings.
        link_string = raw_header.replace(' ', '-')
        for c in ['`', '*', '.']:
            link_string = link_string.replace(c, '')

        link_string = link_string.lower().rstrip()

        toc_line = f"- [{raw_header.rstrip()}](#{link_string})\n"

        toc_string += toc_line

# Write toc to tmp file.
with open('tmp_header.md', 'w') as f:
    f.write(toc_string)