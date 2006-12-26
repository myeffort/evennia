import settings
import time
import functions_general
import functions_db
import functions_help
import global_defines
import session_mgr
import ansi
import os
"""
Generic command module. Pretty much every command should go here for
now.
"""   
def cmd_inventory(cdat):
   """
   Shows a player's inventory.
   """
   session = cdat['session']
   pobject = session.get_pobject()
   session.msg("You are carrying:")
   
   for item in pobject.get_contents():
      session.msg(" %s" % (item,))
      
   money = pobject.get_attribute_value("MONEY", default=0)
   if money > 0:
      money_name = functions_db.get_server_config("MONEY_NAME_PLURAL")
   else:
      money_name = functions_db.get_server_config("MONEY_NAME_SINGULAR")
      
   session.msg("You have %d %s." % (money,money_name))

def cmd_look(cdat):
   """
   Handle looking at objects.
   """
   session = cdat['session']
   pobject = session.get_pobject()
   args = cdat['uinput']['splitted'][1:]

   if len(args) == 0:   
      target_obj = pobject.get_location()
   else:
      results = functions_db.local_and_global_search(pobject, ' '.join(args))
      
      if len(results) > 1:
         session.msg("More than one match found (please narrow target):")
         for result in results:
            session.msg(" %s" % (result,))
         return
      elif len(results) == 0:
         session.msg("I don't see that here.")
         return
      else:
         target_obj = results[0]
   
   retval = "%s%s(#%i%s)\r\n%s" % (
      target_obj.get_ansiname(),
      ansi.ansi["normal"],
      target_obj.id,
      target_obj.flag_string(),
      target_obj.get_description(),
   )
   session.msg(retval)
   
   con_players = []
   con_things = []
   con_exits = []
   
   for obj in target_obj.get_contents():
      if obj.is_player():
         if obj != pobject and obj.is_connected_plr():
            con_players.append(obj)
      elif obj.is_exit():
         con_exits.append(obj)
      else:
         con_things.append(obj)
   
   if con_players:
      session.msg("%sPlayers:%s" % (ansi.ansi["hilite"], ansi.ansi["normal"],))
      for player in con_players:
         session.msg('%s' %(player,))
   if con_things:
      session.msg("%sContents:%s" % (ansi.ansi["hilite"], ansi.ansi["normal"],))
      for thing in con_things:
         session.msg('%s' %(thing,))
   if con_exits:
      session.msg("%sExits:%s" % (ansi.ansi["hilite"], ansi.ansi["normal"],))
      for exit in con_exits:
         session.msg('%s' %(exit,))
         
def cmd_examine(cdat):
   """
   Detailed object examine command
   """
   session = cdat['session']
   pobject = session.get_pobject()
   args = cdat['uinput']['splitted'][1:]
   
   if len(args) == 0:   
      target_obj = pobject.get_location()
   else:
      results = functions_db.local_and_global_search(pobject, ' '.join(args))
      
      if len(results) > 1:
         session.msg("More than one match found (please narrow target):")
         for result in results:
            session.msg(" %s" % (result,))
         return
      elif len(results) == 0:
         session.msg("I don't see that here.")
         return
      else:
         target_obj = results[0]
   session.msg("%s%s(#%i%s)\r\n%s" % (
      target_obj.get_ansiname(fullname=True),
      ansi.ansi["normal"],
      target_obj.id,
      target_obj.flag_string(),
      target_obj.get_description(no_parsing=True),
   ))
   session.msg("Type: %s Flags: %s" % (target_obj.get_type(), target_obj.get_flags()))
   session.msg("Owner: %s " % (target_obj.get_owner(),))
   session.msg("Zone: %s" % (target_obj.get_zone(),))
   
   for attribute in target_obj.get_all_attributes():
      session.msg("%s%s%s: %s" % (ansi.ansi["hilite"], attribute.name, ansi.ansi["normal"], attribute.value))
   
   con_players = []
   con_things = []
   con_exits = []
   
   for obj in target_obj.get_contents():
      if obj.is_player:
         con_players.append(obj)  
      elif obj.is_exit:
         con_exits.append(obj)
      else:
         con_things.append(obj)
   
   if con_players or con_things:
      session.msg("Contents:")
      for player in con_players:
         session.msg('%s' %(player,))
      for thing in con_things:
         session.msg('%s' %(thing,))
         
   if con_exits:
      session.msg("%sExits:%s" % (ansi.ansi["hilite"], ansi.ansi["normal"],))
      for exit in con_exits:
         session.msg('%s' %(exit,))
         
   if not target_obj.is_room():
      if target_obj.is_exit():
         session.msg("Destination: %s" % (target_obj.get_home(),))
      else:
         session.msg("Home: %s" % (target_obj.get_home(),))
         
      session.msg("Location: %s" % (target_obj.get_location(),))
   
def cmd_quit(cdat):
   """
   Gracefully disconnect the user as per his own request.
   """
   session = cdat['session']
   session.msg("Quitting!")
   session.handle_close()
   
def cmd_who(cdat):
   """
   Generic WHO command.
   """
   session_list = session_mgr.get_session_list()
   session = cdat['session']
   pobject = session.get_pobject()
   
   retval = "Player Name        On For Idle   Room    Cmds   Host\n\r"
   for player in session_list:
      if not player.logged_in:
         continue
      delta_cmd = time.time() - player.cmd_last
      delta_conn = time.time() - player.conn_time
      plr_pobject = player.get_pobject()
      
      retval += '%-16s%9s %4s%-3s#%-6d%5d%3s%-25s\r\n' % \
         (plr_pobject.get_name(), \
         # On-time
         functions_general.time_format(delta_conn,0), \
         # Idle time
         functions_general.time_format(delta_cmd,1), \
         # Flags
         '', \
         # Location
         plr_pobject.get_location().id, \
         player.cmd_total, \
         # More flags?
         '', \
         player.address[0])
   retval += '%d Players logged in.' % (len(session_list),)
   
   session.msg(retval)

def cmd_say(cdat):
   """
   Room-based speech command.
   """
   session_list = session_mgr.get_session_list()
   session = cdat['session']
   pobject = session.get_pobject()
   speech = ' '.join(cdat['uinput']['splitted'][1:])
   
   players_present = [player for player in session_list if player.get_pobject().get_location() == session.get_pobject().get_location() and player != session]
   
   retval = "You say, '%s'" % (speech,)
   for player in players_present:
      player.msg("%s says, '%s'" % (pobject.get_name(), speech,))
   
   session.msg(retval)
   
def cmd_help(cdat):
   """
   Help system commands.
   """
   session = cdat['session']
   pobject = session.get_pobject()
   topicstr = ' '.join(cdat['uinput']['splitted'][1:])
   
   if len(topicstr) == 0:
      topicstr = "Help Index"   
   elif len(topicstr) < 2 and not topicstr.isdigit():
      session.msg("Your search query is too short. It must be at least three letters long.")
      return
      
   topics = functions_help.find_topicmatch(topicstr, pobject)      
      
   if len(topics) == 0:
      session.msg("No matching topics found, please refine your search.")
   elif len(topics) > 1:
      session.msg("More than one match found:")
      for result in topics:
         session.msg(" %s" % (result,))
      session.msg("You may type 'help <#>' to see any of these topics.")
   else:   
      topic = topics[0]
      session.msg("\r\n%s%s%s" % (ansi.ansi["hilite"], topic.get_topicname(), ansi.ansi["normal"]))
      session.msg(topic.get_entrytext_ingame())
   
def cmd_version(cdat):
   """
   Version info command.
   """
   session = cdat['session']
   retval = "-"*50 +"\n\r"
   retval += "Evennia %s\n\r" % (global_defines.EVENNIA_VERSION,)
   retval += "-"*50
   session.msg(retval)

def cmd_time(cdat):
   """
   Server local time.
   """
   session = cdat['session']
   session.msg('Current server time : %s' % (time.strftime('%a %b %d %H:%M %Y (%Z)', time.localtime(),)))
   
def cmd_uptime(cdat):
   """
   Server uptime and stats.
   """
   session = cdat['session']
   server = cdat['server']
   start_delta = time.time() - server.start_time
   loadavg = os.getloadavg()
   session.msg('Current server time : %s' % (time.strftime('%a %b %d %H:%M %Y (%Z)', time.localtime(),)))
   session.msg('Server start time   : %s' % (time.strftime('%a %b %d %H:%M %Y', time.localtime(server.start_time),)))
   session.msg('Server uptime       : %s' % functions_general.time_format(start_delta, style=2))
   session.msg('Server load (1 min) : %.2f' % loadavg[0])