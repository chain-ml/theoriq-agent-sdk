"""
Module defining helpers to work with biscuit data.
"""

from biscuit_auth import Biscuit, Rule, Authorizer, BlockBuilder, Fact
from uuid import UUID


# TODO: Add tests


def get_subject_address(biscuit: Biscuit) -> str:
    """Get the subject address defined in the biscuit data."""

    rule = Rule(
        """
        address($address) <- theoriq:subject("agent", $address)
        """
    )

    authorizer = Authorizer()
    authorizer.add_token(biscuit)

    facts = authorizer.query(rule)
    return facts[0].terms[0]


class TheoriqRequest:
    def __init__(self, body_hash: str, from_addr: str, to_addr: str):
        self.body_hash = body_hash
        self.from_addr = from_addr
        self.to_addr = to_addr

    def to_fact(self, req_id: str) -> Fact:
        return Fact(
            "theoriq:request({req_id}, {body_hash}, {from_addr}, {to_addr})",
            {
                "req_id": req_id,
                "body_hash": self.body_hash,
                "from_addr": self.from_addr,
                "to_addr": self.to_addr,
            },
        )


class TheoriqBudget:
    def __init__(self, amount: str, currency: str, voucher: str):
        self.amount = amount
        self.currency = currency
        self.voucher = voucher

    def to_fact(self, req_id: str) -> Fact:
        return Fact(
            "theoriq:budget({req_id}, {amount}, {currency}, {voucher})",
            {
                "req_id": req_id,
                "amount": self.amount,
                "currency": self.currency,
                "voucher": self.voucher,
            },
        )


class RequestFacts:
    def __init__(self, req_id: UUID, request: TheoriqRequest, budget: TheoriqBudget):
        self.req_id = req_id
        self.request = request
        self.budget = budget

    @staticmethod
    def from_biscuit(biscuit: Biscuit) -> "RequestFacts":
        rule = Rule(
            """
            data($req_id, $body_hash, $from_addr, $target_addr, $amount, $currency, $voucher) <- theoriq:request($req_id, $body_hash, $from_addr, $target_addr), theoriq:budget($req_id, $amount, $currency, $voucher)
            """
        )

        authorizer = Authorizer()
        authorizer.add_token(biscuit)
        facts = authorizer.query(rule)

        [req_id, body_hash, from_addr, to_addr, amount, currency, voucher] = map(lambda x: str(x), facts)
        theoriq_req = TheoriqRequest(str(body_hash), str(from_addr), str(to_addr))
        theoriq_budget = TheoriqBudget(amount, currency, voucher)

        return RequestFacts(req_id, theoriq_req, theoriq_budget)

    def to_block(self) -> BlockBuilder:
        block_builder = BlockBuilder("")
        request_id = str(self.req_id)
        block_builder.add_fact(self.request.to_fact(request_id))
        block_builder.add_fact(self.budget.to_fact(request_id))

        return block_builder


class TheoriqResponse:
    def __init__(self, body_hash: str, to_addr: str):
        self.body_hash = body_hash
        self.to_addr = to_addr

    def to_fact(self, req_id: str) -> Fact:
        return Fact(
            "theoriq:response({req_id}, {body_hash}, {to_addr})",
            {"req_id": req_id, "body_hash": self.body_hash, "to_addr": self.to_addr},
        )


class TheoriqCost:
    def __init__(self, amount: str, currency: str):
        self.amount = amount
        self.currency = currency

    def to_fact(self, req_id: str) -> Fact:
        return Fact(
            "theoriq:cost({req_id}, {amount}, {currency})",
            {"req_id": req_id, "amount": self.amount, "currency": self.currency},
        )


class ResponseFacts:
    def __init__(self, req_id: UUID, response: TheoriqResponse, cost: TheoriqCost):
        self.req_id = req_id
        self.response = response
        self.cost = cost

    @staticmethod
    def from_biscuit(biscuit: Biscuit) -> "ResponseFacts":
        rule = Rule(
            """
            data($req_id, $body_hash, $target_addr, $amount, $currency) <- theoriq:response($req_id, $body_hash, $target_addr), theoriq:cost($req_id, $amount, $currency)
            """
        )

        authorizer = Authorizer()
        authorizer.add_token(biscuit)
        facts = authorizer.query(rule)

        [req_id, body_hash, to_addr, amount, currency] = facts
        theoriq_resp = TheoriqResponse(body_hash, to_addr)
        theoriq_cost = TheoriqCost(amount, currency)

        return ResponseFacts(req_id, theoriq_resp, theoriq_cost)

    def to_block(self) -> BlockBuilder:
        block_builder = BlockBuilder("")
        request_id = str(self.req_id)
        block_builder.add_fact(self.response.to_fact(request_id))
        block_builder.add_fact(self.cost.to_fact(request_id))

        return block_builder


def get_request_facts(biscuit: Biscuit) -> RequestFacts:
    return RequestFacts.from_biscuit(biscuit)


def get_response_facts(biscuit: Biscuit) -> ResponseFacts:
    return ResponseFacts.from_biscuit(biscuit)
