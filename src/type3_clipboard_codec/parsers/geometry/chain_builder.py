from typing import Dict, List, Optional

from ...models.geometry import BBox3D, ContourPoint, Point, Type3Node, Type3ObjectChain


def group_nodes_into_chains(nodes: List[Type3Node]) -> List[Type3ObjectChain]:
    chains: List[Type3ObjectChain] = []
    current_chain: Optional[Type3ObjectChain] = None

    for node in nodes:
        if node.header.class_name == "CZone" or current_chain is None:
            current_chain = Type3ObjectChain()
            chains.append(current_chain)

        if node.header.class_name == "CContour" and any(
            n.header.class_name == "CContour" for n in current_chain.nodes
        ):
            current_chain = Type3ObjectChain()
            chains.append(current_chain)

        current_chain.nodes.append(node)
        current_chain.markers.append(node.header.class_name)

    return chains


def register_bbox_by_class(
    bbox_by_class: Dict[str, BBox3D],
    class_name: str,
    bbox: Optional[BBox3D],
) -> None:
    if bbox is None:
        return
    if class_name not in bbox_by_class:
        bbox_by_class[class_name] = bbox


def choose_chain_bbox(
    chain_bbox: Optional[BBox3D],
    bbox_by_class: Dict[str, BBox3D],
) -> Optional[BBox3D]:
    if chain_bbox is not None:
        return chain_bbox
    return (
        bbox_by_class.get("CContour")
        or bbox_by_class.get("CCourbe")
        or bbox_by_class.get("CZone")
    )


def ensure_work_chain_for_contour_index(
    contour_index: int,
    current_work_chain: Type3ObjectChain,
    processed_chains: List[Type3ObjectChain],
) -> Type3ObjectChain:
    if contour_index > 0:
        new_chain = Type3ObjectChain(
            nodes=current_work_chain.nodes,
            markers=current_work_chain.markers,
        )
        processed_chains.append(new_chain)
        return new_chain

    if not processed_chains:
        processed_chains.append(current_work_chain)
    return current_work_chain


def apply_contour_to_chain(
    chain: Type3ObjectChain,
    records: List[ContourPoint],
    source_node_class: str,
    payload_offset: int,
    stream_offset: int,
    raw_contour_bytes: bytes,
) -> None:
    chain.contour_records = records
    chain.points = [Point(x=p.x_mm, y=p.y_mm, z=p.z_mm) for p in records]
    chain.source_node_class = source_node_class
    chain.source_payload_offset = payload_offset
    chain.source_stream_offset = stream_offset
    chain.raw_contour_bytes = raw_contour_bytes


def build_embedded_contour_chain(
    template_chain: Type3ObjectChain,
    records: List[ContourPoint],
    bbox: BBox3D,
    style,
    source_node_class: str,
    payload_offset: int,
    stream_offset: int,
    raw_contour_bytes: bytes,
) -> Type3ObjectChain:
    return Type3ObjectChain(
        nodes=template_chain.nodes,
        markers=template_chain.markers,
        contour_records=records,
        points=[Point(x=p.x_mm, y=p.y_mm, z=p.z_mm) for p in records],
        bbox=bbox,
        style=style,
        source_node_class=source_node_class,
        source_payload_offset=payload_offset,
        source_stream_offset=stream_offset,
        raw_contour_bytes=raw_contour_bytes,
    )
