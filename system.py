import re
from typing import Optional, Any
import networkx as nx
import datetime
from rich.columns import Columns
from rich.console import Console
from rich.tree import Tree
from eots_assets import Welcome, Help


class __FileSystemObject:
    def __init__(self, parts: list) -> None:
        if not parts:
            self.path = ""
            self.name = ""
            self.parts = []
            self.pointer = tuple()
            return

        self.name = parts[-1]
        if len(parts) == 1:
            self.path = f"{'/'.join(parts[:-1])}"
        elif len(parts) > 1:
            self.path = f"/{'/'.join(parts[:-1])}"

        self.parts = parts
        self.pointer = tuple(parts)

    def __str__(self) -> str:
        return f"{'/'.join([''] + self.parts)}"

    def __hash__(self) -> int:
        return hash((self.pointer, type(self)))

    def __eq__(self, other: Any) -> bool:
        return hash(self) == hash(other)

    @classmethod
    def from_string(cls, fullpath: str) -> "__FileSystemObject":
        parts = re.findall(r"[\.\w]+", fullpath)
        if not parts:
            return cls(parts)

        return cls(parts)


class Path(__FileSystemObject):
    def __init__(self, parts: list) -> None:
        super().__init__(parts)
        self.path_size = 0
        self.cumulative_size = 0
        self.name = f"{self.name}/"

    def __str__(self) -> str:
        return f"{'/'.join([''] + self.parts + [''])}"

    @classmethod
    def root(cls) -> "Path":
        return cls([])

    @classmethod
    def join(cls, predecessors: "Path", successors: "Path") -> "Path":
        joined = predecessors.parts + successors.parts
        return cls(joined)


class File(__FileSystemObject):
    def __init__(self, parts: list, size: int = 0) -> None:
        super().__init__(parts)
        self.size = size


class System:
    def __init__(self, file: Optional[str] = "") -> None:
        self.console = Console()
        self.disk_space = 70000000
        self.disk_available = self.disk_space
        self.disk_used = 0
        self.root = Path.root()
        self.fstree = nx.DiGraph()
        self.fstree.add_node(self.root, size=0, cumulative_size=0)
        self.stdin_buffer = None
        self.stdout_buffer = None
        if file:
            with open(file, "r") as f:
                for line in f.readlines():
                    line = re.findall(r"[\./\w]+", line)
                    command = line[0]
                    args = line[1:]
                    self.eval(command, *args)
        self.cwd = self.root

    def __get_path(self, path: str) -> Path:
        if path is None:
            return self.cwd
        if path == "/":
            return self.root
        if path.startswith("/"):
            return Path.from_string(path)
        elif path.startswith(".."):
            return Path.from_string(self.cwd.path)
        else:
            return Path.join(self.cwd, Path.from_string(path))

    def help(self) -> None:
        num_files = 0
        num_paths = 0
        largest_size = 0
        for node in self.fstree.nodes:
            if isinstance(node, File):
                num_files += 1
                if self.fstree.nodes[node]["size"] > largest_size:
                    largest_size += self.fstree.nodes[node]["size"]
                    largest_filepath = str(node)
                    largest_filename = node.name
            else:
                num_paths += 1
        tree = Tree(str(self.cwd), guide_style="blue")
        for u, v in self.fstree.out_edges(self.cwd):
            if isinstance(v, Path):
                tree.add(f"[blue]{v}[/blue]")
            else:
                tree.add(f"[red]{v}[/blue]")
        help_message = Help(
            num_files=num_files,
            num_paths=num_paths,
            largest_filesize=largest_size,
            largest_filepath=largest_filepath,
            largest_filename=largest_filename,
            cwd=str(self.cwd),
            cwd_tree=tree,
        )
        self.stdout_buffer = help_message

    def exit(self) -> None:
        quit()

    def pwd(self) -> None:
        self.stdout_buffer = f"[blue]{self.cwd}[/blue]"

    def mkdir(self, path: str):
        path = self.__get_path(path)
        if path in self.fstree:
            self.stdout_buffer = f"Abort: Path [blue]{path}[/blue] already exists."
            return

        self.fstree.add_node(path, name=path.name, size=0, cumulative_size=0)
        self.fstree.add_edge(self.cwd, path)
        self.stdout_buffer = f"New path created: [blue]{path}[/blue]"

    def fallocate(self, filepath: str, size: int):
        size = int(size)
        parts = self.__get_path(filepath).parts
        file = File(parts)
        if file in self.fstree:
            self.stdout_buffer = f"Abort: File [red]{file}[/red] already exists"
            return
        elif self.disk_used + size > self.disk_available:
            self.stdout_buffer = f"Abort: Disk full. Free at least {size - self.disk_available} bytes and try again."
            return
        self.fstree.add_node(file, objtype=type(File), size=size)
        self.fstree.add_edge(self.cwd, file)
        self.stdout_buffer = f"New file created: [red]{file}[/red]"
        self.disk_used += size
        self.disk_available -= size

    def cd(self, path: str):
        path = self.__get_path(path)
        if path not in self.fstree:
            self.stdout_buffer = f"Abort: No such path [blue]{path}[/blue]"
            return
        self.cwd = path
        self.stdout_buffer = f"Changing path to [blue]{path}[/blue]"

    def ls(self, path: Optional[str] = None) -> None:
        path = self.__get_path(path)
        children = []
        for _path, child in self.fstree.out_edges(path):
            if isinstance(child, Path):
                children.append(f"[blue]{child.name}[/blue]")
            elif isinstance(child, File):
                children.append(f"[red]{child.name}[/red]")
        columns = Columns(children, equal=True)
        self.stdout_buffer = columns

    def rm(self, path: str) -> None:
        path = self.__get_path(path)
        if path is self.root:
            self.stdout_buffer = f":santa: Come on... You don't want to end up on that list, do you? ;) :santa:"
            return
        elif path in self.fstree:
            path = path
        elif File(path.parts) in self.fstree:
            path = File(path.parts)
        else:
            self.stdout_buffer = f"Abort: No such path or file '{path}'"
            return
        disk_used_old = self.disk_used
        tree = [node for node in nx.bfs_tree(self.fstree, path)][::-1]
        self.stdout_buffer = []
        for node in tree:
            self.fstree.remove_edges_from([edge for edge in self.fstree.edges(node)])
            self.disk_used -= self.fstree.nodes[node]["size"]
            self.disk_available += self.fstree.nodes[node]["size"]
            self.fstree.remove_node(node)
            self.stdout_buffer.append(f"Removed {node}")
        self.stdout_buffer.append(
            f"Freed {disk_used_old - self.disk_used} bytes of space. {self.disk_available} bytes remaining."
        )
        self.stdout_buffer = "\n".join(self.stdout_buffer)

    def du(self, as_tree="") -> None:
        if as_tree != "-t":
            as_tree = ""
        path = self.root
        for node in self.fstree.nodes:
            if isinstance(node, Path):
                self.fstree.nodes[node]["size"] = 0
                self.fstree.nodes[node]["cumulative_size"] = 0

        children = [child for child in nx.bfs_tree(self.fstree, path)][::-1]
        for child in children:
            if isinstance(child, Path):
                for _child, _child_obj in self.fstree.out_edges(child):
                    if isinstance(_child_obj, Path):
                        self.fstree.nodes[child]["cumulative_size"] += self.fstree.nodes[_child_obj]["cumulative_size"]
                    elif isinstance(_child_obj, File):
                        self.fstree.nodes[child]["size"] += self.fstree.nodes[_child_obj]["size"]
                        self.fstree.nodes[child]["cumulative_size"] += self.fstree.nodes[_child_obj]["size"]

        if not as_tree:
            stdout = []
            for node in self.fstree.nodes:
                if isinstance(node, Path):
                    stdout.append([self.fstree.nodes[node]["cumulative_size"], f"[blue]{node}[/blue]"])
                elif isinstance(node, File):
                    stdout.append([self.fstree.nodes[node]["size"], f"[red]{node}[/red]"])
            stdout = list(sorted(stdout, key=lambda s: s[0], reverse=True))
            stdout = ["\t".join([str(output[0]), output[1]]) for output in stdout]
            stdout = "\n".join(stdout)
        else:
            children = [successor for successor in nx.bfs_successors(self.fstree, path)]
            trees = {self.root: Tree(f"{self.fstree.nodes[path]['cumulative_size']}\t[blue]{path}", guide_style="blue")}
            for node, edges in children:
                for edge_node in edges:
                    if isinstance(edge_node, Path):
                        trees[edge_node] = Tree(
                            f"{self.fstree.nodes[edge_node]['cumulative_size']}\t[blue]{edge_node.name}",
                            guide_style="blue",
                        )
                        trees[node].add(trees[edge_node])
                    elif isinstance(edge_node, File):
                        trees[node].add(Tree(f"{self.fstree.nodes[edge_node]['size']}\t[red]{edge_node.name}"))
            stdout = trees[self.root]
        self.stdout_buffer = stdout

    def eval(self, command, *args) -> None:
        command = getattr(self, command)
        command(*args)
        self.console.print(self.stdout_buffer)
        self.stdout_buffer = None

    def interactive(self) -> None:
        message = Welcome()
        self.console.print(message)
        arrow = ":arrow_right: "
        while True:
            now = datetime.datetime.now().strftime("%Y-%m-%d")
            prompt = " ".join([now, f"[blue]{self.cwd}", arrow])
            stdin = self.console.input(prompt)
            args = stdin.split(" ")
            command = args[0]
            args = args[1:]
            try:
                self.eval(command, *args)
            except Exception as e:
                if e == "I/O operation on closed file":
                    quit()
                self.console.print_exception(show_locals=True)
                self.console.print("[red]Uh oh! You found a bug! I'm sure the elves will get right on it... :santa:")

    def _solve_part_1(self):
        # Find all directories whose total sizes are < 100000, then find the sum of the total size of these directories.
        # This code is pulled directly from the 'du' method and adapted to solve the puzzle. I'd rather not write full
        # functions for stdout redirections, grep, regex...
        children = [child for child in nx.bfs_tree(self.fstree, self.root)][::-1]
        for child in children:
            if isinstance(child, Path):
                for _child, _child_obj in self.fstree.out_edges(child):
                    if isinstance(_child_obj, Path):
                        self.fstree.nodes[child]["cumulative_size"] += self.fstree.nodes[_child_obj]["cumulative_size"]
                    elif isinstance(_child_obj, File):
                        self.fstree.nodes[child]["size"] += self.fstree.nodes[_child_obj]["size"]
                        self.fstree.nodes[child]["cumulative_size"] += self.fstree.nodes[_child_obj]["size"]

        sizes = [self.fstree.nodes[node]['cumulative_size'] for node in self.fstree.nodes if isinstance(node, Path)]
        return sum(list(filter(lambda s: s < 100000, sizes)))

    def _solve_part_2(self):
        # Determine the smallest path which, if deleted, would free up the 30000000 available disk space required to
        # install a new package.
        minimum_space = 30000000
        disk_needed = minimum_space - self.disk_available
        sizes = [self.fstree.nodes[node]['cumulative_size'] for node in self.fstree.nodes if isinstance(node, Path)]
        sizes = list(sorted(sizes))
        for size in sizes:
            if size > disk_needed:
                return size


if __name__ == "__main__":
    sys = System(file="stdin-sample.txt")
    sys.interactive()
