import json
import re
import os
import sys
import stat

# temporary until we make a Course class
_course = None

def warn(message):
    print("WARNING:",message,file=sys.stderr)

def load_course(top=".", config="course.json", md="README.md"):
    global _course
    if _course: return _course
    with open(os.path.join(top,config)) as f:
        course = json.load(f)
    course.setdefault('parts',{})
    for p in course['order']:
        path = os.path.join(top,p,md)
        fp = os.path.join(top,p,md)
        if os.path.isfile(fp):
            course['parts'][p] = parsef(path)
        else:
            warn('missing '+fp)
    readme = parse_main_readme(os.path.join(top,md))
    _course = {**course,**readme}
    return _course

def parse_main_readme(path="README.md",sumtitle="Summary"):
    d = {}
    with open(path) as f:
        in_sum = False
        title = ""
        summary = ""
        for line in f:
            if title and (summary and not in_sum): break
            if not title and line.startswith('# '):
                title = unmdlink(line[2:].strip())
                continue
            if line.startswith('## '):
                st = line[2:].strip()
                if not sumtitle or (st == sumtitle):
                    in_sum = True
                continue
            if in_sum:
                line = line.strip()
                if in_sum and summary and not line:
                    in_sum = False
                    continue
                if not line:
                    continue
                else:
                    summary += line + ' '
    return {'title':title,'summary':summary} 

def parsef(path):
    with open(path) as f:
        return parse(f.read())

def parse(buf):
    d = {'title': '','parts':[]}
    part_short = None
    in_concepts = False
    pi = -1 
    for line in buf.split('\n'):
        if line.startswith('# '):
            d['title'] = unmdlink(line[2:].strip())
            continue
        if line.startswith('## '):
            part = unmdlink(line.lstrip('## ').strip())
            if part.startswith("Table of Contents"): continue
            pi += 1
            short = title_to_link(part)
            part_short = short
            d['parts'].append({
                'short': short, 'title':part, 'concepts':[]
            })
            continue
        if part_short and line.startswith('> Concepts:'):
            in_concepts = True
            line = line.replace('> Concepts:','')
            for concept in [x.strip() for x in line.split(',')]:
                if concept: 
                    d['parts'][pi]['concepts'].append(concept)
            continue
        if in_concepts:
            if line.startswith('> '):
                line = line.replace('> ','')
                for c in [x.strip() for x in line.split(',')]:
                    if c:
                        d['parts'][pi]['concepts'].append(c)
            else:
                in_concepts = False
    return d

def update_footer(path="README.md",footer=""):
    with open(path,"r+") as f:
        text = f.read()
        text = re.sub("(?s)\n---.*?$", "\n---\n" + footer, text)
        f.seek(0)
        f.write(text)
        f.truncate()
        f.close

        
def title_to_link(title):
    link = re.sub("\s+", "-", title.lower().strip())
    link = re.sub("[^-a-zA-Z0-9]","",link)
    return link

def unmdlink(s):
    s = re.sub('\](\[|\().*?(\]|\))','',s)
    s = re.sub('\[','',s)
    s = re.sub(r'⏫ *','',s)
    s = re.sub(r'⏪ *','',s)
    return s

def create_precommit_hook(top):
    path = os.path.join(top,'.git/hooks/pre-commit')
    if os.path.isfile(path):
        return
    else:
        with open(path,'w') as f:
            print('ghc', file=f)
            st = os.stat(path)
            os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            print("Pre-commit hook created.")
            print("Just git commit or save from now on.")

def toc(course,short=True,concepts=True,bare=False,numbered=True):
    s = 1
    t = ""
    if numbered:
        num = "{0}. "
    else:
        num = "* "
    if bare:
        target = ""
    else:
        target = "/README.md"
    if short:
        base = num + "[**{1}** (`{2}`)]({2}" + target + ")\n"
    else:
        base = num + "[**{1}**]({2}" + target + ")\n"
    for part in course["order"]:
        p = course["parts"][part]
        t += base.format(s,p["title"],part)
        n = 1
        for sub in p["parts"]:
            form = "  {}. [**{}**]({}/README.md#user-content--{})\n"
            _p = p["parts"][n-1]
            title = _p["title"]
            concepts = _p["concepts"]
            t += form.format(n,title,part,title_to_link(title))
            if concepts:
                t += '      <br>💡 ' + ' ◦ '.join(concepts) + '\n'
            n += 1
        s += 1
    return t

def replace_section(head,new,text):
    if re.search('(?s)'+head+'\n+##',text): # empty section
        return re.sub("(?s)"+head+"\n+", head+"\n\n"+new+"\n", text)
    else: 
        return re.sub("(?s)"+head+"\n\s*\n*.*?\n\s*\n", head+"\n\n"+new+"\n", text)

def update_readme(top="."):
    course = load_course(top)
    try:
        readme = os.path.join(top,"README.md")
        with open(readme,"r+") as f:
            text = f.read()
            text = replace_section("## Table of Contents",toc(course),text)
            f.seek(0)
            f.write(text)
            f.truncate()
            f.close
    except KeyError:
        json.dump(course,fp=sys.stdout,indent=2)

def update_json(top="."):
    course = load_course(top)
    j = os.path.join(top,"course.json")
    with open(j,"w") as f:
        json.dump(course,fp=f,indent=2)

def update_footers(top="."):
    course = load_course(top)
    footer=""
    with open(os.path.join(top,"footer.md")) as f:
        footer = f.read()
        f.close()
    for p in course['order']:
        readme = os.path.join(top,p,"README.md")
        update_footer(readme,footer)

def h1link(s,link):
    s = re.sub(r'^(?m)(#) +([^[].*?)$',r'\1 [⏪ \2]('+link+')',s)
    return s

def h2link(s,link):
    s = re.sub(r'^(?m)(##) +((?!Table of Contents)[^[].*?)$',r'\1 [⏫ \2]('+link+')',s)
    return s

def h3link(s,link):
    s = re.sub(r'^(?m)(###) +([^[].*?)$',r'\1 [⏫ \2]('+link+')',s)
    return s

def hunlink(s):
    s = re.sub(r'^(?m)(###?) +\[([^]]+)\]\(.+?\)$',r'\1 \2',s)
    s = re.sub('⏫ ','',s)
    return s

def link_header(path="README.md",main="/README.md"):
    """Links main h1 header to main and h2 and h3 to TOC."""
    with open(path,"r+") as f:
        text = f.read()
        text = h1link(text,main)
        text = hunlink(text)
        text = h2link(text,'#')
        text = h3link(text,'#')
        f.seek(0)
        f.write(text)
        f.truncate()
        f.close

def link_headers(top="."):
    course = load_course(top)
    main = os.path.join(top,"README.md")
    for p in course['order']:
        readme = os.path.join(top,p,"README.md")
        link_header(readme)

def update_toc(path="README.md"):
    parts = []
    part = None
    subs = {}
    toc = ""
    has_toc = False
    with open(path) as f:
        for line in f:
            if line.startswith('## '):
                part = unmdlink(line.lstrip('## ').strip())
                if part.startswith("Table of Contents"):
                    part = None
                    has_toc = True
                    continue
                if not has_toc: return
                parts.append(part)
                subs[part] = []
            if has_toc and part and line.startswith('### '):
                sub = unmdlink(line.lstrip('### ').strip())
                subs[part].append(sub)
        n = 1
        for part in parts:
            form = "{}. [**{}**](#user-content--{})\n"
            toc += form.format(n,part,title_to_link(part))
            s = 1
            for sub in subs[part]:
                toc += " " + form.format(s,sub,title_to_link(sub))
                s += 1
            n += 1
        f.close()
    # TODO eliminate multiple opens
    with open(path,"r+") as f:
        text = f.read()
        text = replace_section("## Table of Contents",toc,text)
        f.seek(0)
        f.write(text)
        f.truncate()
        f.close

def update_tocs(top="."):
    course = load_course(top)
    for p in course['order']:
        readme = os.path.join(top,p,"README.md")
        update_toc(readme)

def update(top="."):
    if not os.path.isfile(os.path.join(top,"course.json")):
        if os.path.isfile(os.path.join("..","course.json")):
            top = ".."
        else:
            warn("Failed to locate course.json file.")
            exit(1)
    try:
        update_readme(top)
        update_json(top)
        update_footers(top)
        update_tocs(top)
        link_headers(top)
        #create_precommit_hook(top)
        print("GitHub Course Updated.")
    except KeyError as e:
        warn("Missing key, need to update course.json? " + str(e))
    
