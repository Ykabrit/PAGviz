#!/usr/bin/python

import pydot
import argparse
import sys
import tempfile

import re

def main():
    parser = argparse.ArgumentParser(description="Simple command to convert a PAG (Partial Ancestral Graph) in a TXT format exported from Tetrad into a DOT format with a color scheme for the different edge types, and output as an image (PNG by default) or DOT file.")

    ### Arguments definition ###
    parser.add_argument("input_file", type=str)
    parser.add_argument("-w", "--white-background", action='store_true', help="Add a white background to the graph instead of OldLace")
    parser.add_argument("-d", "--dot-file", action='store_true', help="Produce a dot file instead of an image")
    parser.add_argument("--format", default='png', help="The format of the image file if you want to use another format than the default PNG. Example: 'svg'")
    output_mode = parser.add_argument_group('output', 'Choose one or more output modes')
    output_mode.add_argument("-f", "--file-output", type=str, help="A path with a filename (without the extension) to save the output to a desired location")
    output_mode.add_argument("-t", "--terminal-output", action='store_true', help="Output the result to stdout")
    ######

    args = parser.parse_args()

    ### Get all the edges from the file as strings ###
    with open(args.input_file) as f:
        lines = f.readlines()
        edges = [re.sub(r'\d+\.', '', l).strip() for l in lines if re.match(r'^\d+\.', l)]
        nodes = [re.match(r'^\(.+\)$', n) and (n[1:-1], False) or (n, True) for n in lines[1].strip().split(';')]
    ######

    ### Parse each edge to get necessary info and build the graph ###
    added_nodes = []
    bgcolor = args.white_background and 'white' or 'OldLace'
    graph = pydot.Dot(args.input_file.split('/')[-1], graph_type='digraph', bgcolor=bgcolor)

    for i, edge in enumerate(edges):
        edge = edge.split(' ')
        edge_nodes = [edge[0], edge[2]]
        
        for edge_node in edge_nodes:
            if edge_node not in nodes:
                added_nodes.append(edge_node)
                observed = [o for n, o in nodes if n==edge_node][0]
                shape = observed and 'box' or 'ellipse'
                graph.add_node(pydot.Node(edge_node, shape=shape))
        
        arrowhead = edge[1][-1]
        arrowhead = arrowhead == '-' and 'none' or arrowhead == '>' and 'normal' or 'odot'
        arrowtail = edge[1][0]
        arrowtail = arrowtail == '-' and 'none' or arrowtail == '<' and 'normal' or 'odot'

        if arrowtail == 'normal':
            color = 'darkgreen'
        elif arrowhead == 'odot':
            color = 'darkred'
        elif arrowtail == 'odot':
            color = 'darkorange'
        else:
            color = 'darkblue'

        if edge[1][0] == '-':
            # For compatibility with DAGs, edge_type can be omitted.
            if len(edge)>3:
                edge_type = (edge[3], edge[4])
            else:
                edge_type = None
                color = 'black'
            dir = 'forward'
        else:
            edge_type = None
            dir = 'both'

        style = ''
        penwidth = 1

        if edge_type:
            if edge_type[0] == 'dd':
                penwidth = 3
            if edge_type[1] == 'pl':
                style = 'dashed'
        
        graph.add_edge(pydot.Edge(edge_nodes[0], edge_nodes[1], dir=dir, arrowtail=arrowtail, arrowhead=arrowhead, style=style, penwidth=penwidth, color=color))
    ######

    ### Output the results according to the provided arguments ###
    if args.file_output:
        if args.dot_file:
            graph.write(f'{args.file_output}.dot')
        else:
            graph.write(f'{args.file_output}.{args.format}', format=args.format)

    if args.terminal_output:
        with tempfile.NamedTemporaryFile(dir=None) as tmp:
            if args.dot_file:
                graph.write(tmp.name)
                with open(tmp.name) as f:
                    sys.stdout.write(f.read())
            else:
                graph.write(tmp.name, format=args.format)
                with open(tmp.name, 'rb') as f:
                    sys.stdout.buffer.write(f.read())
    ######

    if not args.file_output and not args.terminal_output:
        raise Exception('You need to select at least one output mode.')

if __name__ == "__main__":
    main()
