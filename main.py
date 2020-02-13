import gc
gc.enable()
#gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

from upyhome import UpyHome

uph = UpyHome()
uph.configure()
uph.exec('start')

