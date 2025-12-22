from app.crud.base import CRUDBase
from app.models.enquiry import Enquiry
from app.schemas.enquiry import EnquiryCreate, EnquiryUpdate

class CRUDEnquiry(CRUDBase[Enquiry, EnquiryCreate, EnquiryUpdate]):
    pass

enquiry = CRUDEnquiry(Enquiry)
