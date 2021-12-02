# Read file
with open('azure_deployments.md') as f:
    lines = f.readlines()

# Generate toc
toc_string = ''

for line in lines:
    if '#### ' in line:
        raw_header = line.removeprefix('#### ')
        link_string = raw_header.replace(' ', '-')
        link_string = link_string.replace('`', '')
        link_string = link_string.lower().rstrip()

        toc_line = f"- [{raw_header.rstrip()}](#{link_string})\n"

        toc_string += toc_line

# Write toc to tmp file.
with open('tmp_header.md', 'w') as f:
    f.write(toc_string)