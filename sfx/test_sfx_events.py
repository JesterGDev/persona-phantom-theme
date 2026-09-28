import queue, threading, importlib.util, os, sys
src = open("/home/dawar/.local/bin/phantom-thieves-sounds").read()
src = src.replace('if __name__ == "__main__":\n    sys.exit(main())','')
ns = {"__name__":"t"}; exec(compile(src,"sfx","exec"), ns)
HL = ns["HyprlandListener"]

CFG = {"workspace":"true","lock":"true","unlock":"true","focus":"false"}
def run(payloads):
    q = queue.Queue()
    l = HL(q, CFG)
    for p in payloads: l._handle(p)
    out=[]
    while not q.empty(): out.append(q.get())
    return out, l

ok=True
def check(desc, got, want):
    global ok
    good = got==want
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  {desc}: got={got} want={want}")

print("workspace (0.56 plain text):")
got,l = run([b"workspace>>1", b"workspacev2>>1,1", b"workspace>>2", b"workspacev2>>2,2", b"workspace>>1"])
check("priming silent, then one play per real switch (1->2->1)", got, ["workspace","workspace"])
check("last_ws tracked", l.last_ws, "1")

print("duplicate suppression:")
got,l = run([b"workspace>>1", b"workspace>>1", b"workspacev2>>1,1", b"workspace>>2"])
check("repeats ignored", got, ["workspace"])

print("legacy JSON payload:")
got,l = run([b'workspace>>{"name":"1"}', b'workspace>>{"name":"2"}'])
check("json parsed", got, ["workspace"])

print("lock / unlock:")
got,l = run([b"openwindow>>0xabc,1,hyprlock,Lock Screen",
             b"closewindow>>0xabc,1,hyprlock,Lock Screen"])
check("lock then unlock", got, ["lock","unlock"])

print("double open does not re-trigger lock:")
got,l = run([b"openwindow>>0xabc,1,hyprlock,x", b"openwindow>>0xdef,1,hyprlock,y"])
check("no duplicate lock", got, ["lock"])

print("unlock before any lock is ignored:")
got,l = run([b"closewindow>>0xabc,1,hyprlock,x"])
check("no spurious unlock", got, [])

print("ordinary windows never sound:")
got,l = run([b"openwindow>>0x1,2,org.omarchy.agent,Agent",
             b"openwindow>>0x2,2,firefox,Firefox",
             b"closewindow>>0x2,2,firefox,Firefox"])
check("silent", got, [])

print("malformed input is safe:")
got,l = run([b"garbage", b"", b">>", b">>1,2,3", b"workspace>>"])
check("no crash, no output", got, [])

print()
print("ALL PASS" if ok else "FAILURES PRESENT")
sys.exit(0 if ok else 1)
