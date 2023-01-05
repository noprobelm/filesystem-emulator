from dataclasses import dataclass
from rich.rule import Rule
from rich.align import Align
from rich.segment import Segment
from rich.table import Table, Column
from rich.panel import Panel
from rich.text import Text
from rich.console import Console, ConsoleOptions, RenderResult, Group
from rich.tree import Tree


class Welcome:
    def __init__(self):
        with open("banner.txt", "r") as f:
            self.banner = f.read()

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        banner = Text(self.banner, style="blue", justify="center")
        message = []
        message.append(Text("Entering ineractive mode... There's not too much to see here right now.", style="blue"))
        message.append(
            Text(
                "This program was created to solve 'Day 7' of the 2022 Advent of Code challenge. This far exceeds the puzzle's requirements, but I thought it would be fun to experiment... Enjoy."
            )
        )
        command_grid = Table
        yield banner
        for _ in range(2):
            yield Segment.line()
        mode_msg = Text(
            "Interactive Mode\nThere's not much to see here... type 'help' to learn more.", justify="center"
        )
        yield Panel(mode_msg, style="blue")


@dataclass
class Help:
    num_files: int
    num_paths: int
    largest_filename: str
    largest_filepath: str
    largest_filesize: int
    cwd: str
    cwd_tree: Tree

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        about_message = Text.assemble(
            ("\n", ""),
            ("Elf Off The Shelf ", "red italic"),
            ("is a little joke of an emulated operating system I made while solving ", "blue"),
            ("day 7 ", "red"),
            ("of the 2022 ", "blue"),
            ("Advent of Code ", "red italic"),
            ("challenge. ", "blue"),
            (
                "The challenge has the user develop a filesystem-like relational data structure based on puzzle input "
                "and perform some basic calculations on it.",
                "blue",
            ),
            ("\n", ""),
        )
        rule = Rule(style="blue", title="How To Use")
        how_to_use = Text.assemble(
            ("\n", ""),
            (
                "Just try executing some of the commands listed below and to your right. They work as you might expect them to (mostly). ",
                "blue",
            ),
            ("\n\n", ""),
            (
                "Bear in mind this is really just meant to emulate a file system. You can create file system objects (directories and files), navigate through the file tree structure, and delete objects. You can't do much else."
            ),
            ("\n\n", ""),
            ("Tips:", "underline blue"),
            ("\n", ""),
            (
                "- The file system you find yourself in was pre-generated from the Advent of Code puzzle input. The current working directory is displayed in the cmdline prompt"
            ),
            ("\n", ""),
            (
                "- 'du' is probably the most compelling command in this system, although currently it only shows you the full file structure. In addition to producing the standard output seen in the canonical shell version of 'du', it can output a filetree when passed the '-t' flag.\n",
                "blue",
            ),
            (
                "- Hundreds of command use cases, if not more, are not accounted for. If you break something, a postcard will be displayed and promptly mailed to ", ''
            ),
            (
                "123 ELF ROAD, NORTH POLE 88888", 'underline blue'
            ),
            ("\n", ""),
        )
        about_message = Panel(
            Group(about_message, rule, how_to_use), title="About", style="blue", width=int(console.width / 1.5)
        )

        details_message = Text.assemble(
            ("This file system has ", "blue"),
            (f"{self.num_files} ", "red"),
            ("files among ", "blue"),
            (f"{self.num_paths} ", "red"),
            ("paths. ", "blue"),
            ("The largest file in the system is ", "blue"),
            (f"{self.largest_filename} ", "red"),
            ("whose size is ", "blue"),
            (f"{self.largest_filesize} ", "red"),
            ("and has an absolute path of ", "blue"),
            (f"{self.largest_filepath}.", "red"),
            ("\n\n", ""),
            ("The current working directory is ", "blue"),
            (f"{self.cwd}. ", "red"),
            ("The filetree representation of the current working directory and its immediate children are\n", "blue"),
        )
        details = Table.grid()
        details.add_row(details_message)
        details.add_row(self.cwd_tree)
        details = Panel(details, style="blue", title="System Details")
        about_message = Align(about_message, "center", width=console.width)
        commands = Table("Command", "Description", style="blue", show_edge=False)

        commands.add_row("fallocate", "Create a new file at path")
        commands.add_row("mkdir", "Create a new directory at path")
        commands.add_row("ls", "List the contents of the current working directory")
        commands.add_row("cd", "Change the current directory")
        commands.add_row("pwd", "List the name of the current directory")
        commands.add_row("rm", "Remove a specified file")
        commands.add_row("du -t", "List the contents of the filesystem as a filetree with file sizes. -t is optional")
        commands.add_row("help", "Display this help message")
        commands.add_row("exit", "Exit the emulator")
        commands = Panel(commands, style="blue", title="Commands")

        help_grid = Table.grid(Column("File System Details"), Column("Command Table"))
        help_grid.style = "blue"
        help_grid.add_row(details, commands)
        help_grid.show_lines = True
        yield about_message
        yield help_grid