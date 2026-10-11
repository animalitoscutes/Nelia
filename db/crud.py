"""
CRUD Operations for Scriptor Studio in PostgreSQL.
Completely replaces hardcoded templates with dynamic database persistence.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from db.models import Project, Act, Scene, Character, LoreItem


def get_or_create_default_project(db: Session) -> Project:
    project = db.query(Project).first()
    if not project:
        project = Project(
            title="El Proyecto Génesis",
            logline="Un biólogo descubre un código anómalo en el genoma humano antes de que una corporación silencie el laboratorio.",
            mode="screenplay"
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # Crear Acto inicial
        act1 = Act(project_id=project.id, title="ACTO I: EL DETONANTE", order_index=1)
        act2 = Act(project_id=project.id, title="ACTO II: LA CONFRONTACIÓN", order_index=2)
        act3 = Act(project_id=project.id, title="ACTO III: RESOLUCIÓN", order_index=3)
        db.add_all([act1, act2, act3])
        db.commit()

        # Crear Escena 1 inicial real
        scene1 = Scene(
            project_id=project.id,
            act_id=act1.id,
            scene_number=1,
            title="INT. LABORATORIO DE BIOGENÉTICA - NOCHE",
            content="""INT. LABORATORIO DE BIOGENÉTICA - NOCHE

Lámparas halógenas parpadean sobre mesadas de acero inoxidable colmadas de centrífugas y tubos criogénicos. Afuera ruge una tormenta eléctrica.

JULIÁN (38), ojeras profundas, bata manchada de reactivo químico, teclea con urgencia en una terminal de datos antigua.

Una alerta roja parpadea en el monitor: [TRANSFERENCIA: 98%].

JULIÁN
(hacia el interfono, tenso)
Elena, dime que el canal seguro sigue abierto.

INTERFONO (V.O.)
Quedan cuarenta segundos antes del reinicio del cortafuegos. Si no desconectas la unidad ahora, sabrán exactamente desde qué terminal se filtró.

Julián titubea. Mira la unidad de almacenamiento portátil. La barra de progreso alcanza el 99%.

JULIÁN
No me voy sin el registro de pacientes.

ELENA (V.O.)
¡Julián, los guardias del sector B ya están en el elevador!

Un CLIC metálico retumba al final del corredor. Pasos pesados de botas tácticas.

Julián desconecta la unidad de golpe. La pantalla se vuelve negra.

CORTE A:""",
            synopsis="Julián extrae los datos clandestinos del genoma mientras las fuerzas corporativas cierran las salidas del edificio.",
            character_goal="Copiar los registros biológicos confidenciales antes de que el cortafuegos bloquee la terminal.",
            conflict_obstacle="Los guardias tácticos llegan al elevador y el cortafuegos reinicia en 40 segundos.",
            revision_status="⚪ Primer Borrador",
            time_of_day="NOCHE",
            location="Laboratorio Subterráneo Nivel -2",
            cast_members="Julián, Elena (V.O.), Guardias Tácticos",
            notes="Asegurar que el zumbido de los servidores aumente la tensión.",
            order_index=1
        )

        scene2 = Scene(
            project_id=project.id,
            act_id=act1.id,
            scene_number=2,
            title="EXT. CALLES DE LA CIUDAD - AMANECER",
            content="""EXT. CALLES DE LA CIUDAD - AMANECER

Lluvia incesante sobre el asfalto gastado. Julián camina encorvado entre la multitud con la capucha puesta.

Cruza la avenida sorteando taxis viejos. Se detiene frente al escaparate de una tienda de electrónica para comprobar el reflejo detrás de él.

Un SEDÁN NEGRO con cristales tintados avanza a paso de hombre a media cuadra.""",
            synopsis="Julián huye a pie con la memoria cifrada y descubre que un sedán sin matrícula lo está siguiendo.",
            character_goal="Llegar al punto de encuentro seguro sin ser identificado.",
            conflict_obstacle="El vehículo no identificado reduce la marcha a su espalda.",
            revision_status="⚪ Primer Borrador",
            time_of_day="AMANECER",
            location="Avenida República",
            cast_members="Julián, Ocupantes del Sedán",
            notes="Mantener planos cerrados para sensación de paranoia.",
            order_index=2
        )

        db.add_all([scene1, scene2])

        # Personajes iniciales
        char1 = Character(
            project_id=project.id,
            name="Julián",
            role="Protagonista",
            bio="Biólogo molecular de 38 años. Metódico, desconfiado y motivado por la muerte sospechosa de su mentora.",
            dramatic_need="Exponer la verdad sobre los experimentos corporativos sin perder su libertad."
        )
        char2 = Character(
            project_id=project.id,
            name="Elena Vega",
            role="Aliada / Informante",
            bio="Especialista en ciberseguridad. Proporciona acceso a las redes seguras desde el exterior.",
            dramatic_need="Proteger a Julián sin levantar sospechas en su puesto de trabajo."
        )
        db.add_all([char1, char2])

        # Lore inicial
        lore1 = LoreItem(
            project_id=project.id,
            title="Línea de Tiempo del Incidente Químico",
            category="Línea Temporal",
            content="Cronología de los eventos desde la fuga inicial hasta la orden de desalojo del laboratorio."
        )
        db.add(lore1)

        db.commit()
        db.refresh(project)

    return project


def get_scene(db: Session, scene_id: int) -> Optional[Scene]:
    return db.query(Scene).filter(Scene.id == scene_id).first()


def update_scene_content(db: Session, scene_id: int, content: str) -> Optional[Scene]:
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if scene:
        scene.content = content
        db.commit()
        db.refresh(scene)
    return scene


def update_scene_metadata(db: Session, scene_id: int, **kwargs) -> Optional[Scene]:
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if scene:
        for key, val in kwargs.items():
            if hasattr(scene, key):
                setattr(scene, key, val)
        db.commit()
        db.refresh(scene)
    return scene


def create_new_scene(
    db: Session,
    project_id: int,
    act_id: Optional[int] = None,
    title: str = "NUEVA ESCENA",
    synopsis: str = "",
    character_goal: str = "",
    conflict_obstacle: str = "",
    time_of_day: str = "NOCHE",
    location: str = "",
    cast_members: str = "",
    insert_after_scene_id: Optional[int] = None
) -> Scene:
    existing_scenes = db.query(Scene).filter(Scene.project_id == project_id).order_by(Scene.order_index).all()
    count = len(existing_scenes)

    order_idx = count + 1
    scene_num = count + 1

    if insert_after_scene_id:
        target = db.query(Scene).filter(Scene.id == insert_after_scene_id).first()
        if target:
            order_idx = target.order_index + 1
            if not act_id:
                act_id = target.act_id
            for sc in existing_scenes:
                if sc.order_index >= order_idx:
                    sc.order_index += 1
                    sc.scene_number += 1
            scene_num = target.scene_number + 1

    content = f"{title}\n\n"
    new_scene = Scene(
        project_id=project_id,
        act_id=act_id,
        scene_number=scene_num,
        title=title,
        content=content,
        synopsis=synopsis,
        character_goal=character_goal,
        conflict_obstacle=conflict_obstacle,
        time_of_day=time_of_day,
        location=location,
        cast_members=cast_members,
        order_index=order_idx
    )
    db.add(new_scene)
    db.commit()
    db.refresh(new_scene)
    return new_scene


def get_known_locations(db: Session, project_id: int) -> list[str]:
    scenes = db.query(Scene).filter(Scene.project_id == project_id).all()
    locs = set()
    for s in scenes:
        if s.location:
            locs.add(s.location.strip())
        # Extraer de sluglines INT. / EXT.
        parts = s.title.replace("INT./EXT.", "").replace("INT.", "").replace("EXT.", "").split("-")
        if parts:
            cand = parts[0].strip()
            if cand:
                locs.add(cand)
    return sorted(list(locs))



def get_project_acts_and_scenes(db: Session, project_id: int):
    acts = db.query(Act).filter(Act.project_id == project_id).order_by(Act.order_index).all()
    standalone_scenes = db.query(Scene).filter(Scene.project_id == project_id, Scene.act_id.is_(None)).order_by(Scene.order_index).all()
    characters = db.query(Character).filter(Character.project_id == project_id).all()
    lore = db.query(LoreItem).filter(LoreItem.project_id == project_id).all()
    return acts, standalone_scenes, characters, lore


def delete_scene(db: Session, scene_id: int) -> bool:
    """Elimina permanentemente una escena de PostgreSQL."""
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if scene:
        db.delete(scene)
        db.commit()
        return True
    return False


def get_character(db: Session, character_id: int) -> Optional[Character]:
    return db.query(Character).filter(Character.id == character_id).first()


def create_character(
    db: Session,
    project_id: int,
    name: str,
    role: str = "Protagonista",
    bio: str = "",
    dramatic_need: str = "",
    fatal_flaw: str = "",
    dialogue_style: str = "",
    arc: str = ""
) -> Character:
    char = Character(
        project_id=project_id,
        name=name,
        role=role,
        bio=bio,
        dramatic_need=dramatic_need,
        fatal_flaw=fatal_flaw,
        dialogue_style=dialogue_style,
        arc=arc
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    return char


def update_character(db: Session, character_id: int, **kwargs) -> Optional[Character]:
    char = db.query(Character).filter(Character.id == character_id).first()
    if char:
        for k, v in kwargs.items():
            if hasattr(char, k):
                setattr(char, k, v)
        db.commit()
        db.refresh(char)
    return char


def delete_character(db: Session, character_id: int) -> bool:
    char = db.query(Character).filter(Character.id == character_id).first()
    if char:
        db.delete(char)
        db.commit()
        return True
    return False

