# @version 0.3.10

# -------- Interfaces --------
interface ERC721_Interface:
    def transferFrom(_from: address, _to: address, _tokenId: uint256): nonpayable
    def safeTransferFrom(_from: address, _to: address, _tokenId: uint256, _data: Bytes[1024]=b""): nonpayable
    def ownerOf(_tokenId: uint256) -> address: view
    def getApproved(_tokenId: uint256) -> address: view
    def isApprovedForAll(_owner: address, _operator: address) -> bool: view

# -------- Events --------
event NFTListed:
    seller: indexed(address)
    nftAddress: indexed(address)
    tokenId: indexed(uint256)
    price: uint256

event NFTUnlisted:
    seller: indexed(address)
    nftAddress: indexed(address)
    tokenId: indexed(uint256)

event NFTSold:
    buyer: indexed(address)
    seller: indexed(address)
    nftAddress: address
    tokenId: indexed(uint256)
    price: uint256

event ProposalMade:
    proposer: indexed(address)
    nftAddress: indexed(address)
    tokenId: indexed(uint256)
    proposedPrice: uint256

event ProposalCancelled:
    proposer: indexed(address)
    nftAddress: indexed(address)
    tokenId: indexed(uint256)

event ProposalAccepted:
    seller: indexed(address)
    buyer: indexed(address)
    nftAddress: address
    tokenId: indexed(uint256)
    price: uint256

event Withdraw:
    to: indexed(address)
    amount: uint256

# -------- Storage --------
prices: public(HashMap[address, HashMap[uint256, uint256]])
proposals: public(HashMap[address, HashMap[uint256, HashMap[address, uint256]]])

# Listing tracking
listedNFTs: DynArray[address, 10000]
listedTokenIds: DynArray[uint256, 10000]
listedCount: uint256

# Proposal tracking
proposalAddresses: HashMap[address, HashMap[uint256, DynArray[address, 1000]]]
proposalCount: HashMap[address, HashMap[uint256, uint256]]

# Marketplace settings
owner: public(address)
fee_bps: public(uint256)
collected_fees: public(uint256)

MAX_PROPOSALS: constant(uint256) = 1000

# -------- Constructor --------
@external
def __init__():
    self.owner = msg.sender
    self.fee_bps = 500
    self.listedCount = 0

# -------- Internal Helpers --------
@internal
def _is_approved_or_owner_for_market(nft_addr: address, seller: address, tokenId: uint256) -> bool:
    nft: ERC721_Interface = ERC721_Interface(nft_addr)
    if nft.getApproved(tokenId) == self:
        return True
    if nft.isApprovedForAll(seller, self):
        return True
    return False

@internal
def _take_fee(amount: uint256) -> uint256:
    if self.fee_bps == 0:
        return amount
    fee: uint256 = amount * self.fee_bps / 10000
    self.collected_fees += fee
    return amount - fee

@internal
def _remove_listing(nftAddress: address, tokenId: uint256):
    for i in range(10000):
        if i >= self.listedCount:
            break
        if self.listedNFTs[i] == nftAddress and self.listedTokenIds[i] == tokenId:
            last_index: uint256 = self.listedCount - 1
            if i != last_index:
                self.listedNFTs[i] = self.listedNFTs[last_index]
                self.listedTokenIds[i] = self.listedTokenIds[last_index]
            self.listedNFTs.pop()
            self.listedTokenIds.pop()
            self.listedCount -= 1
            break

@internal
def _remove_proposal(nftAddress: address, tokenId: uint256, proposer: address):
    count: uint256 = self.proposalCount[nftAddress][tokenId]
    for i in range(MAX_PROPOSALS):
        if i >= count:
            break
        if self.proposalAddresses[nftAddress][tokenId][i] == proposer:
            last_index: uint256 = count - 1
            if i != last_index:
                self.proposalAddresses[nftAddress][tokenId][i] = self.proposalAddresses[nftAddress][tokenId][last_index]
            self.proposalAddresses[nftAddress][tokenId].pop()
            self.proposalCount[nftAddress][tokenId] -= 1
            break

# -------- Listing --------
@external
def setNFTPrice(nftAddress: address, tokenId: uint256, price: uint256):
    nftContract: ERC721_Interface = ERC721_Interface(nftAddress)
    assert nftContract.ownerOf(tokenId) == msg.sender, "Only owner can list"
    self.prices[nftAddress][tokenId] = price
    self.listedNFTs.append(nftAddress)
    self.listedTokenIds.append(tokenId)
    self.listedCount += 1
    log NFTListed(msg.sender, nftAddress, tokenId, price)

@external
@nonreentrant("lock4")
def unlistNFT(nftAddress: address, tokenId: uint256):
    nftContract: ERC721_Interface = ERC721_Interface(nftAddress)
    assert nftContract.ownerOf(tokenId) == msg.sender, "Only owner can unlist"

    # Refund all proposers if any
    count: uint256 = self.proposalCount[nftAddress][tokenId]
    if count > 0:
        proposers: DynArray[address, MAX_PROPOSALS] = self.proposalAddresses[nftAddress][tokenId]

        for i in range(MAX_PROPOSALS):
            if i >= count:
                break
            proposer: address = proposers[i]
            amount: uint256 = self.proposals[nftAddress][tokenId][proposer]
            if amount > 0:
                self.proposals[nftAddress][tokenId][proposer] = 0
                send(proposer, amount)
                log ProposalCancelled(proposer, nftAddress, tokenId)  # optional: track refunds

        # Clear proposal tracking
        self.proposalAddresses[nftAddress][tokenId] = []
        self.proposalCount[nftAddress][tokenId] = 0

    # Remove listing
    self.prices[nftAddress][tokenId] = 0
    self._remove_listing(nftAddress, tokenId)

    log NFTUnlisted(msg.sender, nftAddress, tokenId)

# -------- Buying --------
@external
@nonreentrant("lock")
@payable
def buyNFT(nftAddress: address, tokenId: uint256):
    price: uint256 = self.prices[nftAddress][tokenId]
    assert price != 0, "Not listed"
    assert msg.value >= price, "Insufficient funds"

    buyer: address = msg.sender
    nftContract: ERC721_Interface = ERC721_Interface(nftAddress)
    seller: address = nftContract.ownerOf(tokenId)
    assert seller != empty(address), "Invalid seller"
    assert self._is_approved_or_owner_for_market(nftAddress, seller, tokenId), "Marketplace not approved"

    seller_amount: uint256 = self._take_fee(price)
    nftContract.transferFrom(seller, buyer, tokenId)
    send(seller, seller_amount)

    if msg.value > price:
        send(buyer, msg.value - price)

    self.prices[nftAddress][tokenId] = 0
    self._remove_listing(nftAddress, tokenId)
    log NFTSold(buyer, seller, nftAddress, tokenId, price)

# -------- Proposals --------
@external
@payable
def proposeNFTPrice(nftAddress: address, tokenId: uint256, proposedPrice: uint256):
    assert msg.value == proposedPrice, "ETH != proposedPrice"
    self.proposals[nftAddress][tokenId][msg.sender] = proposedPrice
    self.proposalAddresses[nftAddress][tokenId].append(msg.sender)
    self.proposalCount[nftAddress][tokenId] += 1
    log ProposalMade(msg.sender, nftAddress, tokenId, proposedPrice)

@external
@nonreentrant("lock2")
def cancelProposalNFTPrice(nftAddress: address, tokenId: uint256):
    proposedPrice: uint256 = self.proposals[nftAddress][tokenId][msg.sender]
    assert proposedPrice > 0, "No proposal"
    self.proposals[nftAddress][tokenId][msg.sender] = 0
    send(msg.sender, proposedPrice)
    self._remove_proposal(nftAddress, tokenId, msg.sender)
    log ProposalCancelled(msg.sender, nftAddress, tokenId)

# -------- Accept Proposal with Refunds --------
@external
@nonreentrant("lock3")
def acceptNFTProposal(nftAddress: address, tokenId: uint256, buyer: address):
    nftContract: ERC721_Interface = ERC721_Interface(nftAddress)
    seller: address = nftContract.ownerOf(tokenId)
    assert seller == msg.sender, "Only owner can accept"
    proposed: uint256 = self.proposals[nftAddress][tokenId][buyer]
    assert proposed != 0, "No proposal from buyer"
    assert self._is_approved_or_owner_for_market(nftAddress, seller, tokenId), "Marketplace not approved"

    # Transfer NFT to buyer
    nftContract.transferFrom(seller, buyer, tokenId)

    # Send seller's amount after fee
    seller_amount: uint256 = self._take_fee(proposed)
    send(seller, seller_amount)

    # Refund all other proposers
    all_proposers: DynArray[address, MAX_PROPOSALS] = self.proposalAddresses[nftAddress][tokenId]
    count: uint256 = self.proposalCount[nftAddress][tokenId]

    for i in range(MAX_PROPOSALS):
        if i >= count:
            break
        p: address = all_proposers[i]
        if p != buyer:
            amount: uint256 = self.proposals[nftAddress][tokenId][p]
            if amount > 0:
                self.proposals[nftAddress][tokenId][p] = 0
                send(p, amount)

    # Clear accepted proposal and remove buyer from proposal list
    self.proposals[nftAddress][tokenId][buyer] = 0
    self._remove_proposal(nftAddress, tokenId, buyer)

    # Remove NFT listing
    self.prices[nftAddress][tokenId] = 0
    self._remove_listing(nftAddress, tokenId)

    log ProposalAccepted(seller, buyer, nftAddress, tokenId, proposed)

# -------- Fees --------
@external
def withdrawFees(to: address):
    assert msg.sender == self.owner, "Only owner"
    amount: uint256 = self.collected_fees
    assert amount > 0, "No fees"
    self.collected_fees = 0
    send(to, amount)
    log Withdraw(to, amount)

@external
def setFeeBps(new_bps: uint256):
    assert msg.sender == self.owner, "Only owner"
    assert new_bps <= 1000
    self.fee_bps = new_bps


@view
@external
def getPrice(nftAddress: address, tokenId: uint256) -> uint256:
    return self.prices[nftAddress][tokenId]

@view
@external
def getProposal(nftAddress: address, tokenId: uint256, proposer: address) -> uint256:
    return self.proposals[nftAddress][tokenId][proposer]

@view
@external
def getAllListedNFTs() -> (DynArray[address, 10000], DynArray[uint256, 10000]):
    return self.listedNFTs, self.listedTokenIds

@view
@external
def getProposalsForNFT(nftAddress: address, tokenId: uint256) -> (DynArray[address, 1000], DynArray[uint256, 1000]):
    proposers: DynArray[address, 1000] = self.proposalAddresses[nftAddress][tokenId]
    prices: DynArray[uint256, 1000] = []
    count: uint256 = self.proposalCount[nftAddress][tokenId]

    for i in range(MAX_PROPOSALS):
        if i >= count:
            break
        prices.append(self.proposals[nftAddress][tokenId][proposers[i]])

    return proposers, prices
