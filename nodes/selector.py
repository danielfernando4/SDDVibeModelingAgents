from state import AgentState


async def selector_node(state: AgentState) -> AgentState:
    redirection_queue = state.get("redirection_queue", [])

    if redirection_queue:
        next_redirection = redirection_queue.pop(0)
        state["redirection_queue"] = redirection_queue
        state["is_redirection"] = True
        state["redirection_source"] = next_redirection["source"]
        state["target_phase"] = next_redirection["target"]
        state["current_redirection"] = {
            "source": next_redirection["source"],
            "summary": next_redirection.get("summary", ""),
            "suggestions": next_redirection.get("suggestions", ""),
        }
        state["user_prompt"] = (
            f"Redirección desde {next_redirection['source']}: "
            f"{next_redirection.get('summary', '')}"
        )

        print(f"\n  ╔══ SELECTOR [REDIRECCIÓN]")
        print(f"  ║  {next_redirection['source']} → {next_redirection['target']}")
        print(f"  ║  resumen: {next_redirection.get('summary', '')[:130]}")
        print(f"  ║  pendientes: {len(redirection_queue)}")
        print(f"  ╚{'═'*52}")
        return state

    state["is_redirection"] = False
    state["redirection_source"] = None
    target_phase = state.get("target_phase", "")
    user_prompt = state.get("user_prompt", "")

    if target_phase == "requirements" and not state.get("product_exists", False):
        print(f"\n  ✗ ERROR: No puedes ir a Requisitos. Producto no existe.")
        state["target_phase"] = ""
        return state

    if target_phase == "design":
        if not state.get("product_exists", False):
            print(f"\n  ✗ ERROR: No puedes ir a Diseño. Producto no existe.")
            state["target_phase"] = ""
            return state
        if not state.get("requirements_exists", False):
            print(f"\n  ✗ ERROR: No puedes ir a Diseño. Requisitos no existen.")
            state["target_phase"] = ""
            return state

    product_icon = "✓" if state.get("product_exists") else "✗"
    requirements_icon = "✓" if state.get("requirements_exists") else "✗"
    design_icon = "✓" if state.get("design_exists") else "✗"

    print(f"\n  ╔══ SELECTOR")
    print(f"  ║  specs: P:{product_icon} R:{requirements_icon} D:{design_icon}  |  fase: {target_phase}")
    print(f"  ║  prompt: \"{user_prompt[:90]}{'...' if len(user_prompt) > 90 else ''}\"")
    print(f"  ╚{'═'*52}")

    return state
