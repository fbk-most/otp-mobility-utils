import osmium
import os
from tempfile import TemporaryDirectory
from pathlib import Path

class BackWayForwardReferenceWriter:
    """ Writer that adds (backward) referenced objects of nodes and ways, 
        and (forward) referencing objects of relations.
        In this way, nodes and ways are reference-complete in the output file, 
        while for relations, recursively, their parent relations is included.

        The collected data is first written into a temporary file and
        the necessary references are tracked internally. When the writer
        is closed, it writes the final file, mixing together the referenced
        objects from the original file and the written data.

        The writer should be used when reproducing the behaviour of the extract function
        of osmium-tools.
    """
    def __init__(self, outfile: str, ref_src: str,
                 overwrite: bool = False, forward_relation_depth: int = 0,
                 backward_relation_depth: int = 1) -> None:

        self.outfile = outfile        
        self.ref_src = ref_src
        self.tmpdir = TemporaryDirectory()
        self.writer_nw = osmium.SimpleWriter(str(Path(self.tmpdir.name, 'back_writer.osm.pbf')))
        self.writer_r = osmium.SimpleWriter(str(Path(self.tmpdir.name, 'forward_writer.osm.pbf')))
        self.overwrite = overwrite
        
        self.id_tracker_nw = osmium.IdTracker()
        self.id_tracker_r = osmium.IdTracker()

        self.forward_relation_depth_r = forward_relation_depth
        self.backward_relation_depth_nw = backward_relation_depth

    def __enter__(self) -> 'BackWayForwardReferenceWriter':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is None:
            self.close()
        else:
            # Exception occured. Do not write out the final file.
            self.writer_r.close()
            self.writer_nw.close()

    def add(self, obj) -> None:
        """ Write an arbitrary OSM object. This can be either an
            osmium object or a Python object that has the appropriate
            attributes.
        """
        if hasattr(obj, 'location'):
            self.id_tracker_nw.add_node(obj.id)
        elif hasattr(obj, 'nodes'):
            self.id_tracker_nw.add_way(obj.id)
        elif hasattr(obj, 'members'):
            self.id_tracker_r.add_relation(obj.id)
        self.writer.add(obj)

    def add_node(self, n) -> None:
        """ Write out an OSM node.
        """
        self.id_tracker_nw.add_node(n.id)
        self.writer_nw.add_node(n)

    def add_way(self, w) -> None:
        """ Write out an OSM way.
        """
        self.id_tracker_nw.add_way(w.id)
        self.writer_nw.add_way(w)

    def add_relation(self, r) -> None:
        """ Write out an OSM relation.
        """
        self.id_tracker_r.add_relation(r.id)
        self.writer_r.add_relation(r)

    def close(self) -> None:
        """ Close the writer and write out the final file.

            The function will be automatically called when the writer
            is used as a context manager.
        """
        # Part 1: Nodes and Ways
        self.writer_nw.close()
        if self.backward_relation_depth_nw > 0:
            self.id_tracker_nw.complete_backward_references(
                self.ref_src,
                relation_depth=self.backward_relation_depth_nw
            )

        # Relations:
        self.writer_r.close()
        if self.forward_relation_depth_r > 0:
            self.id_tracker_r.complete_forward_references(
                self.ref_src,
                relation_depth=self.forward_relation_depth_r)

        fp1_nw = osmium.file_processor.FileProcessor(str(Path(self.tmpdir.name, 'back_writer.osm.pbf')))
        fp2_nw = osmium.file_processor.FileProcessor(self.ref_src).with_filter(self.id_tracker_nw.id_filter())
        
        fp1_r = osmium.file_processor.FileProcessor(str(Path(self.tmpdir.name, 'forward_writer.osm.pbf')))
        fp2_r = osmium.file_processor.FileProcessor(self.ref_src).with_filter(self.id_tracker_r.id_filter())

        with osmium.SimpleWriter(self.outfile, overwrite=self.overwrite) as writer:
            for o1, o2 in osmium.file_processor.zip_processors(fp1_nw, fp2_nw):
                if o1:
                    writer.add(o1)
                else:
                    writer.add(o2)
                        
            for o1, o2 in osmium.file_processor.zip_processors(fp1_r, fp2_r):
                if o1:
                    writer.add(o1)
                else:
                    writer.add(o2)

        self.tmpdir.cleanup()
        self.tmpdir = None