; benchmark generated from python API
(set-info :status unknown)
(declare-fun b () (_ BitVec 16))
(declare-fun y () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(declare-fun c () (_ BitVec 16))
(assert
 (let ((?x17 ((_ extract 15 0) (bvlshr ((_ extract 15 0) a) ((_ zero_extend 0) y)))))
(let ((?x18 ((_ extract 15 0) c)))
(let (($x20 (and (distinct (ite (bvult y (_ bv2 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(and (distinct (ite $x20 (bvadd ?x17 ?x18) b) (ite $x20 (bvadd ?x18 ?x17) b)) true)))))
(check-sat)
