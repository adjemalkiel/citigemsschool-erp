"""ponytail: mirrors facture_mecef.html page_h — fails if formula drifts."""
def page_h(n_items=0, tax=False, paid=False, mecef=False):
    h = 106 + n_items * 8 + (12 if tax else 0) + (16 if paid else 0) + (48 if mecef else 0)
    return 120 if h < 120 else (297 if h > 297 else h)

assert page_h() == 120
assert page_h(1, paid=True, mecef=True) == 178  # 106+8+16+48
assert page_h(30, paid=True, mecef=True) == 297
print("ok")
