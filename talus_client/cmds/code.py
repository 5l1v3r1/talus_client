#!/usr/bin/env python
# encoding: utf-8

import argparse
import cmd
import os
import shlex
import sys
from tabulate import tabulate

from talus_client.cmds import TalusCmdBase
import talus_client.api
import talus_client.errors as errors
from talus_client.models import *

class CodeCmd(TalusCmdBase):
	"""The Talus code command processor
	"""

	command_name = "code"

	def do_list(self, args):
		"""List existing code in Talus. By default it will list both
		components and tools. Note that -t and -c are mutually exclusive

		code list [-t or -c]

		     -t,--tools    List tools (default=False)
		-c,--components    List components (default=False)

		Examples:

		List all components defined in Talus

			code list -t component
		"""
		parser = self._argparser()
		parser.add_argument("--tools", "-t", default=False, action="store_true")
		parser.add_argument("--components", "-c", default=False, action="store_true")

		args = parser.parse_args(shlex.split(args))

		type_ = None
		if args.tools:
			type_ = "tool"

		if args.components:
			# they want to see everything, make it None then
			if type_ is not None:
				type_ = None
			else:
				type_ = "component"

		print(tabulate(self._talus_client.code_iter(type_=type_), headers=Code.headers()))
	
	def do_create(self, args):
		"""Create new code in the repository. This will create the code in the talus
		repository, as well as in the database.

		code create NAME -t or -c

		     -t,--tool    Create a tool
		-c,--component    Create a component
		"""
		args = shlex.split(args)
		parser = self._argparser()
		parser.add_argument("name")
		parser.add_argument("--tool", "-t", default=False, action="store_true")
		parser.add_argument("--component", "-c", default=False, action="store_true")

		args = parser.parse_args(args)

		if not args.tool and not args.component:
			raise errors.TalusApiError("must specify either a tool or a component, non specified")

		if args.tool and args.component:
			raise errors.TalusApiError("must specify either a tool or a component, non both")

		if args.tool:
			code_type = "tool"
		else:
			code_type == "component"

		res = self._talus_client.code_create(
			code_name	= args.name,
			code_type	= code_type
		)
	
	def do_info(self, args):
		"""List the details of a code item (tool or component).

		code info NAME_OR_ID
		"""
		parser = self._argparser()
		parser.add_argument("name_or_id")
		parser.add_argument("--tools", "-t", default=False, action="store_true")
		parser.add_argument("--components", "-c", default=False, action="store_true")

		args = parser.parse_args(shlex.split(args))

		if args.tools and args.components:
			raise errors.TalusApiError("must specify only -t or -c")
			
		search = {}
		if args.tools:
			search["type"] = "tool"
		if args.components:
			search["type"] = "component"

		code = self._talus_client.code_find(args.name_or_id, **search)

		if code is None:
			raise errors.TalusApiError("could not find talus code named {!r}".format(args.name_or_id))

		print("""
    ID: {id}
  Name: {name}
 Bases: {bases}
  Type: {type}
		""".format(
			id		= code.id,
			name	= code.name,
			bases	= " ".join(code.bases),
			type	= code.type.capitalize()
		)[0:-3])
		
		params_nice = []
		for param in code.params:
			if param["type"]["type"] == "native":
				param_type = param["type"]["name"]
			elif param["type"]["type"] == "component":
				param_type = "Component({})".format(param["type"]["name"])
			else:
				param_type = param["type"]["name"]
			params_nice.append([
				param_type,
				param["name"],
				param["desc"]
			])

		params = tabulate(params_nice, headers=["type", "name", "desc"])
		print("Params:\n\n" + "\n".join("    " + p for p in params.split("\n")) + "\n")
