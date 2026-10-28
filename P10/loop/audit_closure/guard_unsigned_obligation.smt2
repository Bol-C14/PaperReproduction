; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 16))
(assert
 (let (($x9 (bvult a (_ bv8 16))))
(and $x9 (= ((_ extract 15 15) a) (_ bv1 1)))))
(check-sat)
