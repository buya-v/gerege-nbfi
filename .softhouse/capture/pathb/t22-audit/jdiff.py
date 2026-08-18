import json,sys
def flat(o,p=''):
    d={}
    if isinstance(o,dict):
        for k,v in o.items(): d.update(flat(v,p+'.'+k))
    elif isinstance(o,list):
        for i,v in enumerate(o): d.update(flat(v,p+'[%d]'%i))
    else: d[p]=o
    return d
a=flat(json.load(open(sys.argv[1])));b=flat(json.load(open(sys.argv[2])))
ks=sorted(set(a)|set(b))
n=0
for k in ks:
    if a.get(k,'<ABSENT>')!=b.get(k,'<ABSENT>'):
        print(k,'|',a.get(k,'<ABSENT>'),'->',b.get(k,'<ABSENT>')); n+=1
print('DIFFS:',n)
