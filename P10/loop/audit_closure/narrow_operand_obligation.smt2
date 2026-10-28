; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 16))
(assert
 (let (($x9 (bvult a (_ bv8 16))))
(and $x9 (and (distinct a ((_ zero_extend 13) ((_ extract 2 0) a))) true))))
(check-sat)
