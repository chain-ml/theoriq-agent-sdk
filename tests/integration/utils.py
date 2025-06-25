from theoriq.api.v1alpha2 import AgentResponse


def agents_are_equal(a: AgentResponse, b: AgentResponse) -> bool:
    return (
        a.system.id == b.system.id
        and a.system.public_key == b.system.public_key
        and a.system.owner_address == b.system.owner_address
        # and a.system.state == b.system.state  # state is different before and after minting
        and a.system.metadata_hash == b.system.metadata_hash
        and a.system.configuration_hash == b.system.configuration_hash
        and a.system.tags == b.system.tags
        and a.metadata.name == b.metadata.name
        and a.metadata.short_description == b.metadata.short_description
        and a.metadata.long_description == b.metadata.long_description
        and a.metadata.tags == b.metadata.tags
        and a.metadata.cost_card == b.metadata.cost_card
        and a.metadata.example_prompts == b.metadata.example_prompts
    )
