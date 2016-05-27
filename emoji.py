# -*- coding: utf-8 -*-
def check_emoji(buf):
	if buf.find('/welcome') == 0:
            return welcome()
            
        if buf.find('/h5') == 0:
            return highFive()
            
        if buf.find('/fight') == 0:
            return fight()
            
        if buf.find('/down') == 0:
            return lieDown()
            
        if buf.find('/confuse') == 0:
            return confuse()
            
        if buf.find('/love') == 0:
            return love()
            
        if buf.find('/cry') == 0:
            return cry()
            
        if buf.find('/angry') == 0:
            return angry()
            
        if buf.find('/happy') == 0:
            return happy()
            
        if buf.find('/awk') == 0:
            return awkward()
        return False

def welcome():
	return '\n\n｡:.ﾟヽ(｡◕◡◕｡)ﾉﾟ.:｡+ﾟ\n'
	
def highFive():
	return '\n\n╭(●｀∀´●)╯╰(●’◡’●)╮\n'

def fight():
	return '\n\n(ง •̀_•́ )ง\n'

def lieDown():
	return '\n\n_(:з」∠)_ _\n'

def confuse():
	return '\n\n（⊙.⊙）?\n'

def love():
	return '\n\n( ˘ ³˘)♥\n'

def cry():
	return '\n\n╥﹏╥\n'

def angry():
	return '\n\n╰（‵□′）╯\n'

def happy():
	return '\n\n╰（￣▽￣）╭\n'

def awkward():
	return '\n\n(“▔□▔)\n'
