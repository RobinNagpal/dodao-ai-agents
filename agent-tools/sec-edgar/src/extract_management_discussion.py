from edgar import *

set_identity("your email")

c = Company("FVR")
filing = c.get_filings(form="10-Q").latest()
tenq = filing.obj()

print(tenq['Item 2'])
