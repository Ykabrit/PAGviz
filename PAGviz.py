#!/usr/bin/python

import pydot
import argparse
import sys
import os
import tempfile

import re


def main():
    parser = argparse.ArgumentParser(
        description="Simple command to convert a PAG (Partial Ancestral Graph) in a TXT format exported from Tetrad into a DOT format with a color scheme for the different edge types, and output as an image or DOT file."
    )

    ### Arguments definition ###
    parser.add_argument("input_file", type=str)
    parser.add_argument(
        "-w",
        "--white-background",
        action="store_true",
        help="Add a white background to the graph instead of OldLace",
    )
    output_mode = parser.add_argument_group("output", "Choose one or more output modes")
    output_mode.add_argument(
        "-f",
        "--file-output",
        type=str,
        help="A path with a filename (with the extension) to save the output to a desired location. If the extension is `.dot`, a DOT file is produced instead of an image. Example: './output_pag.png' or '../dot_files/output_pag.dot'",
    )
    output_mode.add_argument(
        "-t",
        "--terminal-output",
        action="store_true",
        help="Output the result to stdout in the PNG format.",
    )
    ######

    args = parser.parse_args()

    ### Get all the edges from the file as strings ###
    with open(args.input_file) as f:
        lines = f.readlines()
        edges = [
            re.sub(r"\d+\.", "", l).strip() for l in lines if re.match(r"^\d+\.", l)
        ]
        nodes = [
            re.match(r"^\(.+\)$", n) and (n[1:-1], False) or (n, True)
            for n in lines[1].strip().split(";")
        ]
    ######

    ### Create the graph with all the nodes ###
    bgcolor = args.white_background and "white" or "OldLace"
    graph = pydot.Dot(
        args.input_file.split("/")[-1], graph_type="digraph", bgcolor=bgcolor
    )
    for node, observed in nodes:
        shape = observed and "box" or "ellipse"
        graph.add_node(pydot.Node(node, shape=shape))
    ######

    ### Parse each edge to get necessary info and build the graph ###
    for i, edge in enumerate(edges):
        edge = edge.split(" ")
        edge_nodes = [edge[0], edge[2]]

        arrowhead = edge[1][-1]
        arrowhead = (
            arrowhead == "-" and "none" or arrowhead == ">" and "normal" or "odot"
        )
        arrowtail = edge[1][0]
        arrowtail = (
            arrowtail == "-" and "none" or arrowtail == "<" and "normal" or "odot"
        )

        if arrowhead == "normal":
            # <-> OR o-> OR -->
            if arrowtail == "normal":
                # <->
                color = "darkgreen"
            elif arrowtail == "odot":
                # o->
                color = "darkorange"
            else:
                # -->
                color = "darkblue"
        else:
            # o-o OR ---
            color = "darkred"

        if color == "darkblue":
            # if -->
            # For compatibility with DAGs, edge_type can be omitted.
            if len(edge) > 3:
                edge_type = (edge[3], edge[4])
            else:
                # --> edges are colored black if there is no type (DAG or PAG with edge properties not provided).
                edge_type = None
                color = "black"
            dir = "forward"
        else:
            edge_type = None
            dir = "both"

        style = ""
        penwidth = 1

        if edge_type:
            if edge_type[0] == "dd":
                penwidth = 3
            if edge_type[1] == "pl":
                style = "dashed"

        graph.add_edge(
            pydot.Edge(
                edge_nodes[0],
                edge_nodes[1],
                dir=dir,
                arrowtail=arrowtail,
                arrowhead=arrowhead,
                style=style,
                penwidth=penwidth,
                color=color,
            )
        )
    ######

    ### Output the results according to the provided arguments ###
    if args.file_output:
        file_ext = os.path.splitext(args.file_output)[1][1:]
        if file_ext == "dot":
            graph.write(args.file_output)
        else:
            graph.write(args.file_output, format=file_ext)

    if args.terminal_output:
        with tempfile.NamedTemporaryFile(dir=None) as tmp:
            graph.write(tmp.name, format="png")
            with open(tmp.name, "rb") as f:
                sys.stdout.buffer.write(f.read())
    ######

    if not args.file_output and not args.terminal_output:
        raise Exception("You need to select at least one output mode.")


if __name__ == "__main__":
    main()
